import json
import os
import pika
from typing import Any, Dict, Optional


class RabbitMQClient:
    """Client for interacting with RabbitMQ message broker."""

    def __init__(self):
        """Initialize RabbitMQ connection parameters."""
        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.user = os.getenv("RABBITMQ_USER", "dev")
        self.password = os.getenv("RABBITMQ_PASSWORD", "dev")
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ server."""
        if self.connection is None or self.connection.is_closed:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchanges
            self.channel.exchange_declare(
                exchange="transcription", 
                exchange_type="direct",
                durable=True
            )
            
            # Declare queues
            self.channel.queue_declare(
                queue="transcription_tasks", 
                durable=True
            )
            
            # Bind queues to exchanges
            self.channel.queue_bind(
                exchange="transcription",
                queue="transcription_tasks",
                routing_key="transcription"
            )

    def publish_message(
        self, 
        exchange: str, 
        routing_key: str, 
        message: Dict[str, Any],
        properties: Optional[pika.BasicProperties] = None
    ):
        """
        Publish a message to RabbitMQ.
        
        Args:
            exchange: Exchange to publish to
            routing_key: Routing key for the message
            message: Dictionary containing the message data
            properties: Optional message properties
        """
        try:
            self.connect()
            
            if properties is None:
                properties = pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json"
                )
                
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=properties
            )
        except Exception as e:
            print(f"Error publishing message to RabbitMQ: {str(e)}")
            raise
        
    def close(self):
        """Close the connection to RabbitMQ."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.connection = None
            self.channel = None 
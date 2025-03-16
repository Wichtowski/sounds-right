import os
from datetime import UTC, datetime
from celery import Celery
from dotenv import load_dotenv
import json
from container.config import get_config
from database.connection import Database
from database.model.transcription_job import TranscriptionStatus
from repository.storage_repository import StorageRepository
from transcriber.transcriber import Transcriber
from container.container import Container
from flask import request, jsonify

load_dotenv()

# Create the Celery app
app = Celery(
    "sounds-right",
    broker=os.getenv("RABBITMQ_URL", "amqp://dev:dev@rabbitmq:5672/"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Configure task queues
app.conf.task_routes = {
    "transcribe_audio": {"queue": "transcription"},
    "high_priority_task": {"queue": "high_priority"},
    "default_task": {"queue": "default"},
}

# Configure task queues with their own settings
app.conf.task_queues = {
    "transcription": {
        "exchange": "transcription",
        "routing_key": "transcription",
    },
    "high_priority": {
        "exchange": "high_priority",
        "routing_key": "high_priority",
    },
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
}

# Initialize the dependency injection container
container = Container()

# Use container-managed dependencies
config = container.config()
db = container.database()
storage = container.storage_repository()

@app.task(name="transcribe_audio", bind=True)
def transcribe_audio(self, job_id: str, audio_url: str, lyrics: str = None):
    """
    Process a transcription task.
    
    This task is triggered by messages from RabbitMQ.
    """
    try:
        # Get dependencies
        db = container.database()
        storage = container.storage_repository()
        transcriber = container.transcriber()
        
        # Get the job from the database
        job = db.get_transcription_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job status to processing
        job.status = TranscriptionStatus.PROCESSING
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        # Download the file locally
        local_audio_path = storage.download_file(audio_url)
        if not os.path.exists(local_audio_path):
            raise FileNotFoundError(f"Downloaded file not found at {local_audio_path}")

        # Perform transcription
        with open(local_audio_path, "rb") as f:
            audio_data = f.read()
            result = transcriber.transcribe_audio(audio_data, lyrics=lyrics)

        # Clean up temporary file
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        # Update job with results
        job.status = TranscriptionStatus.COMPLETED
        job.result = result.__dict__
        job.updated_at = datetime.now(UTC)
        db.update_transcription_job(job)

        return result.__dict__

    except Exception as e:
        # Handle errors
        if "job" in locals():
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now(UTC)
            db.update_transcription_job(job)

        if "local_audio_path" in locals() and os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        raise

@app.task(queue="high_priority")
def high_priority_task(data):
    return f"Processed high priority task: {data}"

@app.task(queue="default")
def default_task(data):
    return f"Processed default task: {data}"

# Celery beat tasks can be defined here if needed

# RabbitMQ message consumer
@app.task(name="consume_rabbitmq_messages", bind=True)
def consume_rabbitmq_messages(self):
    """
    Consume messages from RabbitMQ and dispatch to appropriate Celery tasks.
    
    This task acts as a bridge between RabbitMQ and Celery.
    """
    try:
        # Get RabbitMQ client
        rabbitmq_client = container.rabbitmq_client()
        rabbitmq_client.connect()
        
        def callback(ch, method, properties, body):
            try:
                # Parse message
                message = json.loads(body)
                task_name = message.get("task")
                
                # Dispatch to appropriate task
                if task_name == "transcribe_audio":
                    transcribe_audio.delay(
                        message.get("job_id"),
                        message.get("audio_url"),
                        message.get("lyrics")
                    )
                elif task_name == "high_priority_task":
                    high_priority_task.delay(message)
                elif task_name == "default_task":
                    default_task.delay(message)
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                # Log error and reject message
                print(f"Error processing message: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Set up consumer
        rabbitmq_client.channel.basic_qos(prefetch_count=1)
        rabbitmq_client.channel.basic_consume(
            queue="transcription_tasks",
            on_message_callback=callback
        )
        
        # Start consuming
        print("Starting to consume messages from RabbitMQ...")
        rabbitmq_client.channel.start_consuming()
        
    except Exception as e:
        print(f"Error in RabbitMQ consumer: {str(e)}")
        raise

if __name__ == "__main__":
    app.start()
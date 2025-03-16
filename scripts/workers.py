from core.celery.app import app, consume_rabbitmq_messages


def start_worker():
    """Start Celery workers"""
    # Start the RabbitMQ consumer in a separate thread
    consume_rabbitmq_messages.delay()
    
    # Start the Celery worker
    argv = [
        "worker",
        "--loglevel=INFO",
        "-Q",
        "transcription,high_priority,default",
        "-n",
        "worker@%h",
    ]
    app.worker_main(argv)


if __name__ == "__main__":
    start_worker()

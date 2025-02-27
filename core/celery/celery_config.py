import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    "sounds-right",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=("tasks",),
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

if __name__ == "__main__":
    app.start()

import os

from celery import Celery
from dotenv import load_dotenv

from core.celery.celery_config import app

load_dotenv()

celery = Celery("tasks")
celery.config_from_object(app.config)

# Optional configuration
celery.conf.update(
    result_expires=3600,
)

if __name__ == "__main__":
    celery.start()

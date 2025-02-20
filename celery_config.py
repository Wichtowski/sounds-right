from celery import Celery

celery = Celery(
    'your_project',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['tasks.transcribe_tasks']  # List your task modules here
)

# Optional configurations
celery.conf.update(
    result_expires=3600,  # Results expire in 1 hour
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == '__main__':
    celery.start() 
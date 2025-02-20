from your_project.celery_config import celery

@celery.task(bind=True)
def transcribe_audio(self, file_path):
    try:
        # Your transcription logic here
        return {"status": "completed", "result": "transcription text"}
    except Exception as e:
        self.retry(exc=e, countdown=60)  # Retry after 1 minute 
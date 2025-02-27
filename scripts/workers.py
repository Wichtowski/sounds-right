from core.celery.celery_config import app


def start_worker():
    """Start Celery workers"""
    argv = [
        "worker",
        "--loglevel=INFO",
        "-Q",
        "high_priority,default",
        "-n",
        "worker@%h",
    ]
    app.worker_main(argv)


if __name__ == "__main__":
    start_worker()

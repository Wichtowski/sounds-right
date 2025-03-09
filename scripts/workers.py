from core.celery.app import celery_config


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

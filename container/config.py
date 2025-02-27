from typing import Dict, Any
import os


def get_config() -> Dict[str, str]:
    return {
        "storage": {
            "review_bucket": "song-transcription-review",
            "production_bucket": "song-transcription",
        },
        "database": {
            "mongo_uri": os.getenv("MONGO_URI"),
            "redis_url": os.getenv("REDIS_URL"),
        },
        "jwt": {
            "secret": os.getenv("JWT_SECRET"),
            "expiry_hours": 24,
        },
    }

from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    return {
        "storage": {
            "review_bucket": "song-transcription-review",
            "production_bucket": "song-transcription"
        },
        "database": {
            "uri": "mongodb://localhost:27017/"
        },
        "jwt": {
            "secret": "your-secret-key",
            "expiry_hours": 24
        }
    } 


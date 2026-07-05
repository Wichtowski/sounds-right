from __future__ import annotations

import asyncio

from sounds_right_worker.logging import get_logger
from sounds_right_worker.storage.minio_client import StorageClient

logger = get_logger(__name__)


async def delete_temp_audio(
    storage: StorageClient,
    bucket: str,
    object_key: str,
) -> bool:
    """Delete the temporary raw audio object. Returns True on success.

    Never raises: cleanup failures should not fail an otherwise successful job.
    """
    try:
        await asyncio.to_thread(storage.delete_object, bucket, object_key)
    except Exception:
        logger.exception(
            "failed to delete temporary audio",
            extra={"bucket": bucket, "object_key": object_key},
        )
        return False
    return True

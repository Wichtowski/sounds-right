from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from sounds_right_worker.config import WorkerSettings
from sounds_right_worker.logging import get_logger

logger = get_logger(__name__)


class ObjectNotFoundError(Exception):
    pass


class StorageError(Exception):
    pass


@dataclass(frozen=True)
class StorageConfig:
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    temp_audio_bucket: str
    transcripts_bucket: str
    artifacts_bucket: str

    @classmethod
    def from_settings(cls, settings: WorkerSettings) -> StorageConfig:
        return cls(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            temp_audio_bucket=settings.minio_temp_audio_bucket,
            transcripts_bucket=settings.minio_transcripts_bucket,
            artifacts_bucket=settings.minio_artifacts_bucket,
        )


class StorageClient:
    """Thin synchronous wrapper around the MinIO client.

    The MinIO SDK is blocking; call these helpers via ``asyncio.to_thread`` from
    async code so the event loop is not blocked.
    """

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )

    def download_to_path(self, bucket: str, object_key: str, destination: Path) -> None:
        try:
            self._client.fget_object(bucket, object_key, str(destination))
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                raise ObjectNotFoundError(object_key) from exc
            raise StorageError(str(exc)) from exc

    def object_exists(self, bucket: str, object_key: str) -> bool:
        try:
            self._client.stat_object(bucket, object_key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return False
            raise StorageError(str(exc)) from exc
        return True

    def upload_json(
        self,
        bucket: str,
        object_key: str,
        data: bytes,
        *,
        content_type: str = "application/json",
    ) -> None:
        try:
            self._client.put_object(
                bucket,
                object_key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as exc:
            raise StorageError(str(exc)) from exc

    def upload_json_document(
        self,
        bucket: str,
        object_key: str,
        document: dict[str, object],
    ) -> bytes:
        data = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
        self.upload_json(bucket, object_key, data)
        return data

    def delete_object(self, bucket: str, object_key: str) -> None:
        try:
            self._client.remove_object(bucket, object_key)
        except S3Error as exc:
            raise StorageError(str(exc)) from exc


def create_storage_client(settings: WorkerSettings) -> StorageClient:
    return StorageClient(StorageConfig.from_settings(settings))

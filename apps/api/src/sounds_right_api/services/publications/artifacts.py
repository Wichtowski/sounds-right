from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from minio import Minio
from minio.error import S3Error

from sounds_right_api.config import ApiSettings
from sounds_right_api.domain.schemas import (
    PublicKaraokeDocument,
    PublicKaraokeManifest,
    TranscriptDocument,
)
from sounds_right_api.models import TrackVersion
from sounds_right_api.services.review import TranscriptMissingError, TranscriptStorageError
from sounds_right_api.storage.minio_client import create_minio_client

from .errors import (
    PublicArtifactMissingError,
    PublicArtifactStorageError,
    PublicationAlreadyExistsError,
)


async def load_internal_transcript(
    version: TrackVersion,
    settings: ApiSettings,
) -> TranscriptDocument:
    if not version.transcript_object_key:
        raise TranscriptMissingError

    client = create_minio_client(settings)
    try:
        response = client.get_object(
            settings.minio_transcripts_bucket,
            version.transcript_object_key,
        )
        try:
            body = response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
            raise TranscriptMissingError from exc
        raise TranscriptStorageError from exc

    try:
        return TranscriptDocument.model_validate(json.loads(body.decode("utf-8")))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise TranscriptStorageError from exc


def ensure_public_bucket(client: Minio, settings: ApiSettings) -> None:
    try:
        if not client.bucket_exists(settings.minio_public_bucket):
            client.make_bucket(settings.minio_public_bucket)
    except S3Error as exc:
        raise PublicArtifactStorageError from exc


def ensure_immutable_objects_absent(
    client: Minio,
    settings: ApiSettings,
    object_keys: list[str],
) -> None:
    for object_key in object_keys:
        try:
            client.stat_object(settings.minio_public_bucket, object_key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
                continue
            raise PublicArtifactStorageError from exc
        raise PublicationAlreadyExistsError


def write_json_object(
    client: Minio,
    settings: ApiSettings,
    object_key: str,
    payload: Any,
) -> None:
    if hasattr(payload, "model_dump_json"):
        body = payload.model_dump_json().encode("utf-8")
    else:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    try:
        client.put_object(
            settings.minio_public_bucket,
            object_key,
            BytesIO(body),
            length=len(body),
            content_type="application/json",
        )
    except S3Error as exc:
        raise PublicArtifactStorageError from exc


def read_public_json[
    PublicJsonModel: (PublicKaraokeManifest, PublicKaraokeDocument, TranscriptDocument)
](
    settings: ApiSettings,
    object_key: str,
    schema: type[PublicJsonModel],
) -> PublicJsonModel:
    client = create_minio_client(settings)
    try:
        response = client.get_object(settings.minio_public_bucket, object_key)
        try:
            body = response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket", "NoSuchObject"}:
            raise PublicArtifactMissingError from exc
        raise PublicArtifactStorageError from exc

    try:
        return schema.model_validate(json.loads(body.decode("utf-8")))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise PublicArtifactStorageError from exc

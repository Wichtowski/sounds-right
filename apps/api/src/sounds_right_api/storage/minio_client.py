from minio import Minio

from sounds_right_api.config import ApiSettings


def create_minio_client(settings: ApiSettings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def create_public_minio_client(settings: ApiSettings) -> Minio:
    return Minio(
        settings.minio_public_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

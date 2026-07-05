from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="sounds-right", alias="APP_NAME")
    database_url: str = Field(alias="DATABASE_URL")
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field(alias="MINIO_PUBLIC_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_temp_audio_bucket: str = Field(alias="MINIO_TEMP_AUDIO_BUCKET")
    minio_transcripts_bucket: str = Field(alias="MINIO_TRANSCRIPTS_BUCKET")
    minio_artifacts_bucket: str = Field(alias="MINIO_ARTIFACTS_BUCKET")
    minio_public_bucket: str = Field(alias="MINIO_PUBLIC_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    upload_url_expires_seconds: int = Field(default=900, alias="UPLOAD_URL_EXPIRES_SECONDS")
    max_audio_upload_size_bytes: int = Field(
        default=100 * 1024 * 1024,
        alias="MAX_AUDIO_UPLOAD_SIZE_BYTES",
    )
    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_client_id: str = Field(default="sounds-right-local", alias="KAFKA_CLIENT_ID")
    kafka_topic: str = Field(default="sounds-right.events", alias="KAFKA_TOPIC")
    kafka_api_consumer_group: str = Field(
        default="sounds-right-projector",
        alias="KAFKA_API_CONSUMER_GROUP",
    )
    api_enable_projector: bool = Field(default=True, alias="API_ENABLE_PROJECTOR")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    cors_allowed_origins: str = Field(
        default="http://localhost:8080,http://localhost:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()  # type: ignore[call-arg]

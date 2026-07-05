from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    worker_name: str = Field(default="sounds-right-worker", alias="WORKER_NAME")

    # Kafka / Redpanda
    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_client_id: str = Field(default="sounds-right-worker-local", alias="KAFKA_CLIENT_ID")
    kafka_topic: str = Field(default="sounds-right.events", alias="KAFKA_TOPIC")
    kafka_worker_consumer_group: str = Field(
        default="sounds-right-workers",
        alias="KAFKA_WORKER_CONSUMER_GROUP",
    )

    # Mock mode
    worker_mock_mode: bool = Field(default=False, alias="WORKER_MOCK_MODE")
    worker_mock_should_fail: bool = Field(default=False, alias="WORKER_MOCK_SHOULD_FAIL")
    worker_mock_step_delay_seconds: float = Field(
        default=1,
        alias="WORKER_MOCK_STEP_DELAY_SECONDS",
    )

    # MinIO
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_temp_audio_bucket: str = Field(alias="MINIO_TEMP_AUDIO_BUCKET")
    minio_transcripts_bucket: str = Field(alias="MINIO_TRANSCRIPTS_BUCKET")
    minio_artifacts_bucket: str = Field(alias="MINIO_ARTIFACTS_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # Audio limits
    max_audio_size_bytes: int = Field(default=104857600, alias="MAX_AUDIO_SIZE_BYTES")
    max_audio_duration_seconds: float = Field(
        default=900,
        alias="MAX_AUDIO_DURATION_SECONDS",
    )

    # Temp files
    worker_temp_root: str = Field(default="/tmp/sounds-right", alias="WORKER_TEMP_ROOT")
    worker_keep_temp_files: bool = Field(default=False, alias="WORKER_KEEP_TEMP_FILES")

    # whisper.cpp
    whisper_cpp_path: str = Field(
        default="/usr/local/bin/whisper-cli",
        alias="WHISPER_CPP_PATH",
    )
    whisper_model_path: str = Field(
        default="/models/ggml-base.bin",
        alias="WHISPER_MODEL_PATH",
    )
    whisper_model_name: str = Field(default="base", alias="WHISPER_CPP_MODEL_NAME")
    whisper_language: str = Field(default="auto", alias="WHISPER_CPP_LANGUAGE")
    whisper_threads: int = Field(default=4, alias="WHISPER_CPP_THREADS")
    whisper_timeout_seconds: int = Field(default=1800, alias="WHISPER_CPP_TIMEOUT_SECONDS")

    # ffmpeg / ffprobe
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    ffprobe_path: str = Field(default="ffprobe", alias="FFPROBE_PATH")

    # Transcript output
    transcript_schema_version: str = Field(default="1.0", alias="TRANSCRIPT_SCHEMA_VERSION")
    transcript_object_prefix: str = Field(
        default="transcripts",
        alias="TRANSCRIPT_OBJECT_PREFIX",
    )

    @field_validator("whisper_cpp_path", "whisper_model_path", "worker_temp_root")
    @classmethod
    def expand_user_path(cls, value: str) -> str:
        return str(Path(value).expanduser())

    @property
    def whisper_cpp_binary(self) -> Path:
        return Path(self.whisper_cpp_path)

    @property
    def whisper_model_file(self) -> Path:
        return Path(self.whisper_model_path)


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()  # type: ignore[call-arg]

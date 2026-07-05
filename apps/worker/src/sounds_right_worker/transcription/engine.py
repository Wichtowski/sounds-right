from __future__ import annotations

from sounds_right_worker.config import WorkerSettings
from sounds_right_worker.transcription.whisper_cpp import WhisperCppConfig, WhisperCppEngine


def create_engine(settings: WorkerSettings) -> WhisperCppEngine:
    return WhisperCppEngine(
        WhisperCppConfig(
            binary=settings.whisper_cpp_binary,
            model=settings.whisper_model_file,
            threads=settings.whisper_threads,
            timeout_seconds=settings.whisper_timeout_seconds,
            default_language=settings.whisper_language,
        )
    )

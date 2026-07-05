from __future__ import annotations

# Stable error codes surfaced in transcription.failed events.
# Messages built from these must remain safe for UI display.

AUDIO_NOT_FOUND = "audio_not_found"
AUDIO_DOWNLOAD_FAILED = "audio_download_failed"
AUDIO_VALIDATION_FAILED = "audio_validation_failed"
AUDIO_TOO_LARGE = "audio_too_large"
AUDIO_DURATION_TOO_LONG = "audio_duration_too_long"
UNSUPPORTED_AUDIO_FORMAT = "unsupported_audio_format"
UNSUPPORTED_OPTION = "unsupported_option"
NORMALIZATION_FAILED = "normalization_failed"
WHISPER_CPP_MISSING = "whisper_cpp_missing"
WHISPER_CPP_FAILED = "whisper_cpp_failed"
TRANSCRIPT_PARSE_FAILED = "transcript_parse_failed"
ARTIFACT_UPLOAD_FAILED = "artifact_upload_failed"
TEMP_CLEANUP_FAILED = "temp_cleanup_failed"
UNKNOWN_WORKER_ERROR = "unknown_worker_error"

# Error codes that should be considered safe to retry.
RETRYABLE_ERROR_CODES = frozenset(
    {
        AUDIO_DOWNLOAD_FAILED,
        ARTIFACT_UPLOAD_FAILED,
        UNKNOWN_WORKER_ERROR,
    }
)


class PipelineError(Exception):
    """Raised inside the transcription pipeline to signal a mapped failure.

    Carries a stable ``error_code`` and a UI-safe ``message`` while allowing the
    full internal exception to be logged separately.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        stage: str,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.stage = stage
        self.retryable = error_code in RETRYABLE_ERROR_CODES if retryable is None else retryable

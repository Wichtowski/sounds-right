from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sounds_right_worker.transcription.schemas import (
    Transcript,
    TranscriptEngine,
    TranscriptMetadata,
    TranscriptSegment,
    TranscriptWord,
    WhisperCppResult,
)


def _count_words(text: str) -> int:
    return len(text.split())


def build_transcript(
    result: WhisperCppResult,
    *,
    schema_version: str,
    track_version_id: uuid.UUID,
    job_id: uuid.UUID,
    engine_name: str,
    model: str,
    duration_seconds: float,
    created_at: datetime | None = None,
) -> Transcript:
    """Normalize a whisper.cpp result into the transcript schema v1."""
    created = created_at or datetime.now(UTC)

    segments: list[TranscriptSegment] = []
    text_parts: list[str] = []
    word_count = 0

    for index, segment in enumerate(result.segments):
        segment_text = segment.text.strip()
        text_parts.append(segment_text)
        word_count += _count_words(segment_text)
        words = [
            TranscriptWord(
                word=word.word,
                start=word.start,
                end=word.end,
                confidence=word.confidence,
            )
            for word in segment.words
        ]
        segments.append(
            TranscriptSegment(
                id=index,
                start=segment.start,
                end=segment.end,
                text=segment_text,
                words=words,
            )
        )

    full_text = " ".join(part for part in text_parts if part).strip()

    return Transcript(
        schema_version=schema_version,
        track_version_id=track_version_id,
        job_id=job_id,
        engine=TranscriptEngine(
            name=engine_name,
            model=model,
            language=result.language,
        ),
        metadata=TranscriptMetadata(
            duration_seconds=duration_seconds,
            created_at=created,
            word_count=word_count,
            segment_count=len(segments),
        ),
        text=full_text,
        segments=segments,
    )

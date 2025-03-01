import os
import whisper
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .vocal_separator import VocalSeparator

@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    duration: float
    language: str
    segments: list[Dict[str, Any]]

class Transcriber:
    def __init__(self, model: whisper.Whisper):
        self.model = model
        self.vocal_separator = VocalSeparator()
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    @staticmethod
    def clean_text(text: str) -> str:
        return text.replace("\n", " ").strip()

    @staticmethod
    def align_lyrics_with_timestamps(lyrics: Optional[str], segments: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        if not lyrics:
            return segments

        words = [word for line in lyrics.splitlines() for word in line.split()]
        aligned_segments, word_index = [], 0

        for segment in segments:
            new_words = []
            for word_data in segment.get("words", []):
                if word_index < len(words):
                    new_words.append({
                        "word": words[word_index],
                        "start": word_data["start"],
                        "end": word_data["end"],
                    })
                    word_index += 1
                else:
                    break

            aligned_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": " ".join(w["word"] for w in new_words),
                "words": new_words,
            })

        return aligned_segments

    def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None, lyrics: Optional[str] = None, separate_vocals: bool = True) -> TranscriptionResult:
        """
        Transcribe audio data using Whisper model and align with lyrics if provided.
        
        Args:
            audio_data: Raw audio data in bytes
            language: Optional language code (e.g., 'en', 'es')
            lyrics: Optional lyrics text for alignment
            separate_vocals: Whether to separate vocals from music before transcription
            
        Returns:
            TranscriptionResult containing the transcription and metadata
        """
        try:
            # Separate vocals if requested
            if separate_vocals:
                audio_data = self.vocal_separator.separate_vocals(audio_data)

            with open("/tmp/audio_to_transcribe.mp3", "wb") as f:
                f.write(audio_data)

            audio = whisper.load_audio("/tmp/audio_to_transcribe.mp3")
            duration = len(audio) / whisper.audio.SAMPLE_RATE
            
            # Detect language if not provided
            if not language:
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
                _, probs = self.model.detect_language(mel)
                language = max(probs, key=probs.get)

            result = self.model.transcribe(
                audio,
                language=language,
                task="transcribe",
                word_timestamps=True,
                fp16=False
            )

            # Align with lyrics if provided
            segments = self.align_lyrics_with_timestamps(lyrics, result["segments"])

            # Calculate confidence
            confidence = (
                np.mean([s.get('confidence', 0.0) for s in result.get('segments', [])])
                if 'segments' in result
                else 0.95
            )

            return TranscriptionResult(
                text=result["text"],
                confidence=float(confidence),
                duration=float(duration),
                language=language,
                segments=segments
            )

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def __del__(self):
        """Cleanup any resources if needed"""
        if os.path.exists("/tmp/audio_to_transcribe.mp3"):
            os.remove("/tmp/audio_to_transcribe.mp3") 
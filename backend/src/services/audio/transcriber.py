"""
Audio transcriber implementation using Whisper for audio transcription.
"""

from typing import Dict, Any, List
from pathlib import Path
import whisper
import torch
from pydantic import BaseModel

from ...core.config import Settings
from ...core.exceptions import AudioTranscriptionError
from ...core.logging import get_logger

logger = get_logger(__name__)

class TranscriptionResult(BaseModel):
    """Model for transcription results."""
    text: str
    segments: list
    language: str
    duration: float

class AudioTranscriber:
    """Transcriber for converting audio to text using Whisper."""

    def __init__(self, settings: Settings):
        """Initialize the audio transcriber."""
        self.settings = settings
        self.model = self._load_model()

    def _load_model(self) -> whisper.Whisper:
        """Load the Whisper model."""
        try:
            model_name = self.settings.whisper_model_name or "base"
            device = "cuda" if torch.cuda.is_available() else "cpu"
            return whisper.load_model(model_name, device=device)
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise AudioTranscriptionError(f"Failed to load Whisper model: {str(e)}")

    async def transcribe_audio(self, audio_file: Path) -> Dict[str, Any]:
        """Transcribe an audio file to text."""
        try:
            # Transcribe audio using Whisper
            result = self.model.transcribe(str(audio_file))
            
            # Convert result to our model
            transcription = TranscriptionResult(
                text=result["text"],
                segments=result["segments"],
                language=result["language"],
                duration=result.get("duration", 0.0)
            )
            
            return transcription.dict()

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise AudioTranscriptionError(f"Failed to transcribe audio: {str(e)}")

    async def transcribe_segment(self, audio_file: Path, start_time: float, end_time: float) -> Dict[str, Any]:
        """Transcribe a specific segment of an audio file."""
        try:
            # Load audio
            audio = whisper.load_audio(str(audio_file))
            
            # Extract segment
            segment = audio[int(start_time * 16000):int(end_time * 16000)]
            
            # Transcribe segment
            result = self.model.transcribe(segment)
            
            return {
                "text": result["text"],
                "start": start_time,
                "end": end_time,
                "language": result["language"]
            }

        except Exception as e:
            logger.error(f"Error transcribing audio segment: {str(e)}")
            raise AudioTranscriptionError(f"Failed to transcribe audio segment: {str(e)}")

    async def detect_language(self, audio_file: Path) -> str:
        """Detect the language of an audio file."""
        try:
            # Load audio
            audio = whisper.load_audio(str(audio_file))
            
            # Detect language
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            
            return max(probs, key=probs.get)

        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            raise AudioTranscriptionError(f"Failed to detect language: {str(e)}")

    async def generate_timestamps(self, audio_file: Path) -> List[Dict[str, Any]]:
        """Generate word-level timestamps for an audio file."""
        try:
            # Transcribe with word timestamps
            result = self.model.transcribe(
                str(audio_file),
                word_timestamps=True
            )
            
            return result["words"]

        except Exception as e:
            logger.error(f"Error generating timestamps: {str(e)}")
            raise AudioTranscriptionError(f"Failed to generate timestamps: {str(e)}") 
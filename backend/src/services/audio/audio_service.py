from typing import List, Optional
from pathlib import Path
import asyncio
from datetime import datetime
from pydantic import BaseModel

from ..base_service import BaseService
from ...core.exceptions import AudioProcessingError

class AudioConfig(BaseModel):
    """Configuration for audio service."""
    watch_directory: Path
    output_directory: Path
    supported_formats: List[str] = ["mp3", "wav", "m4a", "ogg"]
    check_interval: int = 300  # 5 minutes
    whisper_model: str = "base"
    batch_size: int = 16
    device: str = "cpu"
    language: Optional[str] = None

class TranscriptionResult(BaseModel):
    """Model for transcription results."""
    audio_file: Path
    text: str
    segments: List[dict]
    language: str
    duration: float
    note_path: Optional[Path] = None
    created_at: datetime = datetime.now()

class AudioService(BaseService):
    """Service for processing and transcribing audio files."""

    def _initialize(self) -> None:
        """Initialize audio service configuration and resources."""
        self.config_model = AudioConfig(**self.config)
        self._whisper_model = None
        self._background_task = None
        self._running = False
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.config_model.watch_directory.mkdir(parents=True, exist_ok=True)
        self.config_model.output_directory.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the audio processing service."""
        if self._running:
            return

        try:
            import whisper
            self._whisper_model = whisper.load_model(
                self.config_model.whisper_model,
                device=self.config_model.device
            )
        except ImportError as e:
            raise AudioProcessingError("Failed to load Whisper model: whisper not installed") from e
        except Exception as e:
            raise AudioProcessingError(f"Failed to load Whisper model: {str(e)}") from e

        self._running = True
        self._background_task = asyncio.create_task(self._process_audio_periodically())

    async def stop(self) -> None:
        """Stop the audio processing service."""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def health_check(self) -> bool:
        """Check if the audio service is healthy."""
        return self._whisper_model is not None and self._running

    async def _process_audio_periodically(self) -> None:
        """Periodically process new audio files."""
        while self._running:
            try:
                await self._process_new_audio_files()
            except Exception as e:
                raise AudioProcessingError(f"Error processing audio files: {str(e)}")
            finally:
                await asyncio.sleep(self.config_model.check_interval)

    async def _process_new_audio_files(self) -> List[TranscriptionResult]:
        """Process new audio files in the watch directory."""
        results = []
        for file_format in self.config_model.supported_formats:
            for audio_file in self.config_model.watch_directory.glob(f"*.{file_format}"):
                try:
                    result = await self._transcribe_audio(audio_file)
                    note_path = await self._create_note_from_transcription(result)
                    result.note_path = note_path
                    results.append(result)
                    # Move processed file to output directory
                    new_path = self.config_model.output_directory / audio_file.name
                    audio_file.rename(new_path)
                except Exception as e:
                    raise AudioProcessingError(f"Error processing {audio_file}: {str(e)}")
        return results

    async def _transcribe_audio(self, audio_file: Path) -> TranscriptionResult:
        """Transcribe an audio file using Whisper."""
        try:
            result = self._whisper_model.transcribe(
                str(audio_file),
                language=self.config_model.language,
                batch_size=self.config_model.batch_size
            )
            return TranscriptionResult(
                audio_file=audio_file,
                text=result["text"],
                segments=result["segments"],
                language=result["language"],
                duration=result.get("duration", 0.0)
            )
        except Exception as e:
            raise AudioProcessingError(f"Transcription failed for {audio_file}: {str(e)}")

    async def _create_note_from_transcription(self, result: TranscriptionResult) -> Path:
        """Create an Obsidian note from transcription results."""
        # Implementation for creating notes from transcription
        pass 
from typing import List, Optional, Dict, Any
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

    def __init__(self, context=None, processor=None, transcriber=None, config: Optional[Dict[str, Any]] = None):
        """Initialize the audio service.
        
        Args:
            context: The service context
            processor: The audio processor instance
            transcriber: The audio transcriber instance
            config (Optional[Dict[str, Any]]): Service configuration dictionary
        """
        self.context = context
        self.processor = processor
        self.transcriber = transcriber
        super().__init__(config)

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

    async def process_audio(self, audio_path: Path) -> TranscriptionResult:
        """Process an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            TranscriptionResult: The transcription result
        """
        if not await self.validate_audio(audio_path):
            raise AudioProcessingError(f"Invalid audio file: {audio_path}")
        
        try:
            result = await self.transcribe_audio(audio_path)
            metadata = await self.extract_metadata(audio_path)
            result.metadata = metadata
            return result
        except Exception as e:
            raise AudioProcessingError(f"Failed to process audio: {str(e)}")

    async def transcribe_audio(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            TranscriptionResult: The transcription result
        """
        if not self.transcriber:
            raise AudioProcessingError("No transcriber available")
        
        try:
            return await self.transcriber.transcribe(audio_path)
        except Exception as e:
            raise AudioProcessingError(f"Failed to transcribe audio: {str(e)}")

    async def extract_metadata(self, audio_path: Path) -> Dict[str, Any]:
        """Extract metadata from an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            Dict[str, Any]: The extracted metadata
        """
        try:
            return await self.processor.extract_metadata(audio_path)
        except Exception as e:
            raise AudioProcessingError(f"Failed to extract metadata: {str(e)}")

    async def convert_format(self, audio_path: Path, target_format: str) -> Path:
        """Convert an audio file to a different format.
        
        Args:
            audio_path (Path): Path to the audio file
            target_format (str): Target format extension
            
        Returns:
            Path: Path to the converted file
        """
        if target_format not in self.config_model.supported_formats:
            raise AudioProcessingError(f"Unsupported format: {target_format}")
        
        try:
            return await self.processor.convert_format(audio_path, target_format)
        except Exception as e:
            raise AudioProcessingError(f"Failed to convert audio format: {str(e)}")

    async def split_audio(self, audio_path: Path, segments: List[Dict[str, float]]) -> List[Path]:
        """Split an audio file into segments.
        
        Args:
            audio_path (Path): Path to the audio file
            segments (List[Dict[str, float]]): List of segment timestamps
            
        Returns:
            List[Path]: List of paths to the segment files
        """
        try:
            return await self.processor.split_audio(audio_path, segments)
        except Exception as e:
            raise AudioProcessingError(f"Failed to split audio: {str(e)}")

    async def merge_audio(self, audio_paths: List[Path]) -> Path:
        """Merge multiple audio files.
        
        Args:
            audio_paths (List[Path]): List of audio file paths
            
        Returns:
            Path: Path to the merged file
        """
        try:
            return await self.processor.merge_audio(audio_paths)
        except Exception as e:
            raise AudioProcessingError(f"Failed to merge audio: {str(e)}")

    async def analyze_audio(self, audio_path: Path) -> Dict[str, Any]:
        """Analyze an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            return await self.processor.analyze_audio(audio_path)
        except Exception as e:
            raise AudioProcessingError(f"Failed to analyze audio: {str(e)}")

    async def detect_silence(self, audio_path: Path) -> List[Dict[str, float]]:
        """Detect silence segments in an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            List[Dict[str, float]]: List of silence segments
        """
        try:
            return await self.processor.detect_silence(audio_path)
        except Exception as e:
            raise AudioProcessingError(f"Failed to detect silence: {str(e)}")

    async def normalize_audio(self, audio_path: Path, target_level: float) -> Path:
        """Normalize audio volume.
        
        Args:
            audio_path (Path): Path to the audio file
            target_level (float): Target normalization level
            
        Returns:
            Path: Path to the normalized file
        """
        try:
            return await self.processor.normalize_audio(audio_path, target_level)
        except Exception as e:
            raise AudioProcessingError(f"Failed to normalize audio: {str(e)}")

    async def batch_process(self, audio_paths: List[Path]) -> List[TranscriptionResult]:
        """Process multiple audio files in batch.
        
        Args:
            audio_paths (List[Path]): List of audio file paths
            
        Returns:
            List[TranscriptionResult]: List of transcription results
        """
        results = []
        for audio_path in audio_paths:
            try:
                result = await self.process_audio(audio_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {audio_path}: {str(e)}")
        return results

    async def validate_audio(self, audio_path: Path) -> bool:
        """Validate an audio file.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not audio_path.exists():
            return False
        
        if audio_path.suffix[1:] not in self.config_model.supported_formats:
            return False
        
        try:
            await self.processor.validate_audio(audio_path)
            return True
        except Exception:
            return False

    async def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.
        
        Returns:
            List[str]: List of supported formats
        """
        return self.config_model.supported_formats

    async def get_transcription_languages(self) -> List[str]:
        """Get list of supported transcription languages.
        
        Returns:
            List[str]: List of supported languages
        """
        if not self.transcriber:
            raise AudioProcessingError("No transcriber available")
        return await self.transcriber.get_supported_languages() 
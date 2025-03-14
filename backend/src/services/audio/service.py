"""
Main audio service implementation for DiscoSui.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime
from pydantic import BaseModel

from ...core.config import Settings
from ...core.exceptions import AudioServiceError
from ...core.logging import get_logger
from .transcriber import AudioTranscriber
from .processor import AudioProcessor

logger = get_logger(__name__)

class AudioMetadata(BaseModel):
    """Audio metadata model."""
    filename: str
    duration: float
    date: str
    tags: List[str]
    categories: List[str]

class AudioService:
    """Main service for handling audio processing and transcription."""

    def __init__(self, settings: Settings):
        """Initialize the audio service."""
        self.settings = settings
        self.transcriber = AudioTranscriber(settings)
        self.processor = AudioProcessor(settings)
        self.vault_path = Path(settings.vault_path)
        self.audio_path = self.vault_path / "Audio"
        self._ensure_audio_directory()

    def _ensure_audio_directory(self):
        """Ensure the audio directory exists in the vault."""
        self.audio_path.mkdir(parents=True, exist_ok=True)

    async def process_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an audio file and create a note with its transcription."""
        try:
            # Transcribe audio
            transcription = await self.transcriber.transcribe_audio(file_path)
            
            # Process transcription
            processed = await self.processor.process_transcription(transcription)
            
            # Create note
            note_path = await self._create_audio_note(file_path, processed)
            
            return {
                "transcription": processed,
                "note_path": str(note_path)
            }

        except Exception as e:
            logger.error(f"Error processing audio file: {str(e)}")
            raise AudioServiceError(f"Failed to process audio file: {str(e)}")

    async def _create_audio_note(self, audio_file: Path, transcription_data: Dict[str, Any]) -> Path:
        """Create a note for the processed audio in the vault."""
        try:
            metadata = AudioMetadata(
                filename=audio_file.name,
                duration=transcription_data["duration"],
                date=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                tags=self._generate_tags(audio_file, transcription_data),
                categories=self._categorize_audio(transcription_data)
            )
            
            # Generate note content using template
            note_content = self.processor.generate_note_content(
                audio_file,
                transcription_data,
                metadata
            )
            
            # Create note file
            note_path = self.audio_path / f"{metadata.date}_{audio_file.stem}.md"
            note_path.write_text(note_content)
            
            return note_path

        except Exception as e:
            logger.error(f"Error creating audio note: {str(e)}")
            raise AudioServiceError(f"Failed to create audio note: {str(e)}")

    def _generate_tags(self, audio_file: Path, transcription_data: Dict[str, Any]) -> List[str]:
        """Generate tags for the audio file based on content and metadata."""
        tags = ["#Audio"]
        
        # Add file type tag
        file_type = audio_file.suffix.lstrip(".")
        tags.append(f"#FileType/{file_type}")
        
        # Add duration-based tag
        duration = transcription_data["duration"]
        if duration < 300:  # 5 minutes
            tags.append("#Duration/Short")
        elif duration < 1800:  # 30 minutes
            tags.append("#Duration/Medium")
        else:
            tags.append("#Duration/Long")
        
        return tags

    def _categorize_audio(self, transcription_data: Dict[str, Any]) -> List[str]:
        """Categorize audio based on transcription content."""
        categories = []
        
        # Add basic categories based on content
        text = transcription_data["text"].lower()
        if any(word in text for word in ["meeting", "discussion", "call"]):
            categories.append("Meetings")
        elif any(word in text for word in ["note", "reminder", "todo"]):
            categories.append("Notes")
        elif any(word in text for word in ["idea", "brainstorm", "concept"]):
            categories.append("Ideas")
        
        return categories

    async def search_audio_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search for audio notes in the vault."""
        try:
            return await self.processor.search_audio_notes(query)
        except Exception as e:
            logger.error(f"Error searching audio notes: {str(e)}")
            raise AudioServiceError(f"Failed to search audio notes: {str(e)}")

    async def get_audio_metadata(self, note_path: str) -> AudioMetadata:
        """Get metadata for an audio note."""
        try:
            return await self.processor.get_audio_metadata(note_path)
        except Exception as e:
            logger.error(f"Error getting audio metadata: {str(e)}")
            raise AudioServiceError(f"Failed to get audio metadata: {str(e)}")

    async def update_audio_categories(self, note_path: str, categories: List[str]):
        """Update categories for an audio note."""
        try:
            await self.processor.update_categories(note_path, categories)
        except Exception as e:
            logger.error(f"Error updating audio categories: {str(e)}")
            raise AudioServiceError(f"Failed to update audio categories: {str(e)}")

    async def cleanup_old_audio(self, days: Optional[int] = None):
        """Clean up old audio notes based on retention policy."""
        try:
            await self.processor.cleanup_old_audio(days)
        except Exception as e:
            logger.error(f"Error cleaning up old audio: {str(e)}")
            raise AudioServiceError(f"Failed to clean up old audio: {str(e)}") 
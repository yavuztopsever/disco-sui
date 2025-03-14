from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import whisper
from pydantic import BaseModel, Field
from ..base_service import BaseService
from ...core.config import Settings
from ...core.obsidian_utils import ObsidianUtils
from ...core.exceptions import AudioProcessingError

class AudioMetadata(BaseModel):
    """Metadata for processed audio files."""
    filename: str = Field(..., description="Original audio filename")
    duration: float = Field(..., description="Audio duration in seconds")
    date_processed: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    language: str = Field(..., description="Detected language")
    model_used: str = Field(..., description="Whisper model used for transcription")

class AudioTranscriber(BaseService):
    """Service for transcribing audio files and integrating them into the Obsidian vault."""

    def _initialize(self) -> None:
        """Initialize audio transcriber service resources."""
        self.settings = Settings()
        self.obsidian_utils = ObsidianUtils()
        self.audio_dir = Path(self.settings.AUDIO_FILES_DIR)
        self.vault_path = Path(self.settings.VAULT_PATH)
        self.model = whisper.load_model("base")  # Can be configured in settings
        
        # Create necessary directories
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'audio_transcripts').mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the audio transcription service."""
        try:
            await self.process_pending_audio()
        except Exception as e:
            raise AudioProcessingError(f"Failed to start audio processing: {str(e)}")

    async def stop(self) -> None:
        """Stop the audio transcription service."""
        # Cleanup resources if needed
        pass

    async def health_check(self) -> bool:
        """Check if the audio transcription service is healthy."""
        return (
            self.audio_dir.exists() and
            self.vault_path.exists() and
            self.model is not None
        )

    async def process_pending_audio(self) -> None:
        """Process all pending audio files in the input directory."""
        supported_formats = ('.mp3', '.wav', '.m4a', '.ogg')
        for audio_file in self.audio_dir.glob("*"):
            if audio_file.suffix.lower() in supported_formats:
                try:
                    await self.process_audio_file(audio_file)
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Error processing audio {audio_file}: {str(e)}")

    async def process_audio_file(self, audio_path: Path) -> None:
        """Process a single audio file and create corresponding note.
        
        Args:
            audio_path: Path to the audio file
        """
        # Transcribe audio
        result = self.model.transcribe(str(audio_path))
        
        # Extract metadata
        metadata = self._extract_metadata(audio_path, result)
        
        # Create note content
        note_content = self._create_note_content(result, metadata)
        
        # Create note in vault
        note_path = self._get_note_path(metadata)
        await self.obsidian_utils.write_note(note_path, note_content)
        
        # Move processed audio to archive if configured
        if self.settings.ARCHIVE_PROCESSED_AUDIO:
            archive_path = self.vault_path / 'audio_archive' / audio_path.name
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.rename(archive_path)

    def _extract_metadata(self, audio_path: Path, result: Dict[str, Any]) -> AudioMetadata:
        """Extract metadata from transcription result.
        
        Args:
            audio_path: Path to the audio file
            result: Whisper transcription result
            
        Returns:
            AudioMetadata object
        """
        return AudioMetadata(
            filename=audio_path.name,
            duration=result.get('duration', 0.0),
            language=result.get('language', 'unknown'),
            model_used=self.model.model_name
        )

    def _create_note_content(self, result: Dict[str, Any], metadata: AudioMetadata) -> str:
        """Create note content from transcription result.
        
        Args:
            result: Whisper transcription result
            metadata: Audio metadata
            
        Returns:
            Formatted note content
        """
        content = []
        
        # Add frontmatter
        content.append('---')
        content.append('type: audio_transcript')
        content.append(f'source_file: {metadata.filename}')
        content.append(f'duration: {metadata.duration}')
        content.append(f'language: {metadata.language}')
        content.append(f'date_processed: {metadata.date_processed.isoformat()}')
        content.append(f'model: {metadata.model_used}')
        content.append('---\n')
        
        # Add title and metadata
        content.append(f'# Audio Transcript: {metadata.filename}\n')
        content.append('## Metadata\n')
        content.append(f'- **Duration**: {int(metadata.duration // 60)}m {int(metadata.duration % 60)}s')
        content.append(f'- **Language**: {metadata.language}')
        content.append(f'- **Processed**: {metadata.date_processed.strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        # Add transcription
        content.append('## Transcription\n')
        content.append(result['text'])
        
        # Add segments with timestamps if available
        if 'segments' in result:
            content.append('\n## Detailed Segments\n')
            for segment in result['segments']:
                timestamp = f"[{int(segment['start']//60)}:{int(segment['start']%60):02d}]"
                content.append(f"{timestamp} {segment['text']}")
        
        # Add summary and key points (if LLM integration is enabled)
        if hasattr(self, 'llm') and self.settings.ENABLE_LLM_ANALYSIS:
            summary = self._generate_summary(result['text'])
            content.append('\n## Summary\n')
            content.append(summary['summary'])
            content.append('\n## Key Points\n')
            for point in summary['key_points']:
                content.append(f'- {point}')
            content.append('\n## Action Items\n')
            for item in summary['action_items']:
                content.append(f'- [ ] {item}')
        
        return '\n'.join(content)

    def _get_note_path(self, metadata: AudioMetadata) -> Path:
        """Generate path for audio transcript note.
        
        Args:
            metadata: Audio metadata
            
        Returns:
            Path object for note location
        """
        date_str = metadata.date_processed.strftime('%Y-%m-%d')
        safe_filename = metadata.filename.rsplit('.', 1)[0]
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in (' ', '-', '_'))
        filename = f"{date_str} - {safe_filename} - Transcript.md"
        return self.vault_path / 'audio_transcripts' / filename

    def _generate_summary(self, text: str) -> Dict[str, Any]:
        """Generate summary and extract key points using LLM.
        
        Args:
            text: Transcribed text
            
        Returns:
            Dictionary containing summary, key points, and action items
        """
        # This is a placeholder for LLM integration
        # In a real implementation, this would use the configured LLM to generate
        # a summary, extract key points, and identify action items
        return {
            'summary': 'LLM integration required for summary generation',
            'key_points': ['LLM integration required for key points extraction'],
            'action_items': ['LLM integration required for action items identification']
        } 
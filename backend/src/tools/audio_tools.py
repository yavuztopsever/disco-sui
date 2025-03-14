from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import whisper
import os
import json
from datetime import datetime

class TranscribeAudioTool(BaseTool):
    name = "transcribe_audio"
    description = "Transcribe an audio file and create a note with the transcription"
    inputs = {
        "audio_path": {
            "type": "string",
            "description": "The path to the audio file, relative to the vault root"
        },
        "note_title": {
            "type": "string",
            "description": "The title for the transcription note",
            "nullable": True
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the note",
            "nullable": True
        },
        "model_size": {
            "type": "string",
            "description": "The size of the Whisper model to use",
            "default": "base",
            "enum": ["tiny", "base", "small", "medium", "large"]
        }
    }
    output_type = "object"

    def forward(self, audio_path: str, note_title: Optional[str] = None, folder: Optional[str] = None, model_size: str = "base") -> Dict[str, Any]:
        try:
            # Validate paths
            if not self._validate_path(audio_path):
                raise ValueError(f"Invalid audio path: {audio_path}")

            # Get full paths
            audio_file_path = self._get_full_path(audio_path)

            # Check if audio file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Generate note title if not provided
            if not note_title:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                note_title = f"Transcription_{timestamp}"

            # Create folder if specified
            note_folder = self._get_full_path(folder) if folder else self.vault_path
            self._ensure_path_exists(note_folder)

            # Load Whisper model
            model = whisper.load_model(model_size)

            # Transcribe audio
            result = model.transcribe(audio_file_path)

            # Prepare note content
            content = f"# {note_title}\n\n"
            content += f"## Transcription\n\n{result['text']}\n\n"
            content += f"## Metadata\n\n"
            content += f"- Audio File: {audio_path}\n"
            content += f"- Model: {model_size}\n"
            content += f"- Duration: {result['duration']:.2f} seconds\n"
            content += f"- Language: {result['language']}\n"

            # Add segments if available
            if 'segments' in result:
                content += "\n## Segments\n\n"
                for segment in result['segments']:
                    content += f"- [{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}\n"

            # Create frontmatter
            frontmatter = {
                "title": note_title,
                "type": "transcription",
                "audio_file": audio_path,
                "transcription_date": datetime.now().isoformat(),
                "model": model_size,
                "duration": result['duration'],
                "language": result['language']
            }

            # Create note
            note_path = os.path.join(note_folder, f"{note_title}.md")
            content = self._update_frontmatter(content, frontmatter)
            self._write_file(note_path, content)

            return {
                "success": True,
                "message": f"Audio file '{audio_path}' transcribed and saved to note '{note_title}'",
                "path": os.path.relpath(note_path, self.vault_path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to transcribe audio: {str(e)}",
                "error": str(e)
            }

class ListAudioFilesTool(BaseTool):
    name = "list_audio_files"
    description = "List all audio files in the vault"
    inputs = {
        "folder": {
            "type": "string",
            "description": "Optional folder path to list audio files from",
            "nullable": True
        },
        "extensions": {
            "type": "array",
            "description": "List of audio file extensions to include",
            "default": [".mp3", ".wav", ".m4a", ".ogg"],
            "items": {
                "type": "string"
            }
        }
    }
    output_type = "object"

    def forward(self, folder: Optional[str] = None, extensions: List[str] = [".mp3", ".wav", ".m4a", ".ogg"]) -> Dict[str, Any]:
        try:
            # Get the target directory
            target_dir = self._get_full_path(folder) if folder else self.vault_path

            # Validate path
            if not self._validate_path(target_dir):
                raise ValueError(f"Invalid folder path: {folder}")

            # List audio files
            audio_files = []
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if any(file.lower().endswith(ext.lower()) for ext in extensions):
                        rel_path = os.path.relpath(os.path.join(root, file), self.vault_path)
                        audio_files.append(rel_path)

            return {
                "success": True,
                "audio_files": audio_files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list audio files: {str(e)}",
                "error": str(e)
            }

class GetTranscriptionNoteTool(BaseTool):
    name = "get_transcription_note"
    description = "Get the transcription note associated with an audio file"
    inputs = {
        "audio_path": {
            "type": "string",
            "description": "The path to the audio file, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, audio_path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(audio_path):
                raise ValueError(f"Invalid audio path: {audio_path}")

            # Search for transcription notes
            transcription_notes = []
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        content = self._read_file(file_path)
                        frontmatter = self._get_frontmatter(content)
                        
                        # Check if this is a transcription note for the audio file
                        if (frontmatter.get('type') == 'transcription' and 
                            frontmatter.get('audio_file') == audio_path):
                            rel_path = os.path.relpath(file_path, self.vault_path)
                            transcription_notes.append(rel_path)

            if not transcription_notes:
                return {
                    "success": False,
                    "message": f"No transcription note found for audio file '{audio_path}'"
                }

            return {
                "success": True,
                "transcription_notes": transcription_notes
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get transcription note: {str(e)}",
                "error": str(e)
            } 
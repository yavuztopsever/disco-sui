"""Note management functionality."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class NoteManager:
    """Manages note operations in the Obsidian vault."""

    def __init__(self, vault_path: Path):
        """Initialize the note manager.

        Args:
            vault_path: Path to the Obsidian vault.
        """
        self.vault_path = vault_path

    def create_note(self, title: str, content: str, folder: Optional[str] = None) -> Path:
        """Create a new note in the vault.

        Args:
            title: Title of the note.
            content: Content of the note.
            folder: Optional folder path within the vault.

        Returns:
            Path to the created note.
        """
        # Create folder if it doesn't exist
        note_path = self.vault_path
        if folder:
            note_path = note_path / folder
            note_path.mkdir(parents=True, exist_ok=True)

        # Create note file
        note_path = note_path / f"{title}.md"
        note_path.write_text(content)
        return note_path

    def get_note(self, title: str, folder: Optional[str] = None) -> Optional[str]:
        """Get the content of a note.

        Args:
            title: Title of the note.
            folder: Optional folder path within the vault.

        Returns:
            Content of the note if found, None otherwise.
        """
        note_path = self.vault_path
        if folder:
            note_path = note_path / folder
        note_path = note_path / f"{title}.md"

        if note_path.exists():
            return note_path.read_text()
        return None

    def update_note(self, title: str, content: str, folder: Optional[str] = None) -> bool:
        """Update an existing note.

        Args:
            title: Title of the note.
            content: New content for the note.
            folder: Optional folder path within the vault.

        Returns:
            True if the note was updated, False if it doesn't exist.
        """
        note_path = self.vault_path
        if folder:
            note_path = note_path / folder
        note_path = note_path / f"{title}.md"

        if note_path.exists():
            note_path.write_text(content)
            return True
        return False

    def delete_note(self, title: str, folder: Optional[str] = None) -> bool:
        """Delete a note.

        Args:
            title: Title of the note.
            folder: Optional folder path within the vault.

        Returns:
            True if the note was deleted, False if it doesn't exist.
        """
        note_path = self.vault_path
        if folder:
            note_path = note_path / folder
        note_path = note_path / f"{title}.md"

        if note_path.exists():
            note_path.unlink()
            return True
        return False

    def list_notes(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all notes in a folder.

        Args:
            folder: Optional folder path within the vault.

        Returns:
            List of dictionaries containing note information.
        """
        search_path = self.vault_path
        if folder:
            search_path = search_path / folder

        notes = []
        if search_path.exists():
            for note_path in search_path.glob("*.md"):
                notes.append({
                    "title": note_path.stem,
                    "path": str(note_path.relative_to(self.vault_path)),
                    "modified": datetime.fromtimestamp(note_path.stat().st_mtime).isoformat()
                })
        return notes 
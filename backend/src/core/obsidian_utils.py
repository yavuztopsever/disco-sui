import os
from pathlib import Path
import yaml
from typing import Dict, Optional, List
from jinja2 import Environment, FileSystemLoader
from ..core.exceptions import (
    NoteNotFoundError,
    NoteAlreadyExistsError,
    FolderNotFoundError,
    FrontmatterError,
    ObsidianIOError
)
from ..core.config import settings

class ObsidianUtils:
    def __init__(self):
        self.vault_path = Path(settings.VAULT_PATH)
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.vault_path / "templates"))
        )

    def get_note_path(self, note_name: str) -> Path:
        """Get the full path for a note."""
        return self.vault_path / f"{note_name}.md"

    def read_note(self, note_path: str) -> str:
        """Read the contents of a note."""
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise NoteNotFoundError(f"Note not found: {note_path}")
        except Exception as e:
            raise ObsidianIOError(f"Error reading note {note_path}: {str(e)}")

    def write_note(self, note_path: str, content: str) -> None:
        """Write content to a note."""
        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise ObsidianIOError(f"Error writing note {note_path}: {str(e)}")

    def get_frontmatter(self, note_content: str) -> Dict:
        """Extract frontmatter from note content."""
        try:
            if not note_content.startswith('---'):
                return {}
            
            parts = note_content.split('---', 2)
            if len(parts) < 3:
                return {}
            
            return yaml.safe_load(parts[1])
        except Exception as e:
            raise FrontmatterError(f"Error parsing frontmatter: {str(e)}")

    def update_frontmatter(self, note_content: str, new_frontmatter: Dict) -> str:
        """Update frontmatter in note content."""
        try:
            if not note_content.startswith('---'):
                return f"---\n{yaml.dump(new_frontmatter)}---\n\n{note_content}"
            
            parts = note_content.split('---', 2)
            if len(parts) < 3:
                return f"---\n{yaml.dump(new_frontmatter)}---\n\n{note_content}"
            
            return f"---\n{yaml.dump(new_frontmatter)}---{parts[2]}"
        except Exception as e:
            raise FrontmatterError(f"Error updating frontmatter: {str(e)}")

    def render_template(self, template_name: str, context: Dict) -> str:
        """Render a Jinja2 template with context."""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise ObsidianIOError(f"Error rendering template {template_name}: {str(e)}")

    def create_folder(self, folder_path: str) -> None:
        """Create a folder in the vault."""
        try:
            Path(folder_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ObsidianIOError(f"Error creating folder {folder_path}: {str(e)}")

    def move_file(self, source: str, destination: str) -> None:
        """Move a file within the vault."""
        try:
            Path(source).rename(destination)
        except Exception as e:
            raise ObsidianIOError(f"Error moving file from {source} to {destination}: {str(e)}")

    def open_note(self, note_path: str) -> None:
        """Open a note in Obsidian."""
        try:
            # This will be implemented to integrate with Obsidian's API
            pass
        except Exception as e:
            raise ObsidianIOError(f"Error opening note {note_path}: {str(e)}")

    def open_node(self, note_path: str, node_id: str) -> None:
        """Open a specific node in a note in Obsidian."""
        try:
            # This will be implemented to integrate with Obsidian's API
            pass
        except Exception as e:
            raise ObsidianIOError(f"Error opening node {node_id} in note {note_path}: {str(e)}")

    def get_note_links(self, note_path: str) -> List[str]:
        """Get all links from a note."""
        try:
            content = self.read_note(note_path)
            # Implement link extraction logic
            return []
        except Exception as e:
            raise ObsidianIOError(f"Error getting links from note {note_path}: {str(e)}")

    def get_note_tags(self, note_path: str) -> List[str]:
        """Get all tags from a note."""
        try:
            content = self.read_note(note_path)
            # Implement tag extraction logic
            return []
        except Exception as e:
            raise ObsidianIOError(f"Error getting tags from note {note_path}: {str(e)}") 
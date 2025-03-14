from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from ...core.obsidian_utils import ObsidianUtils
from ...core.exceptions import (
    NoteNotFoundError,
    NoteAlreadyExistsError,
    TemplateNotFoundError,
    FrontmatterError
)

class NoteMetadata(BaseModel):
    """Model for note metadata."""
    title: str
    tags: List[str] = []
    type: str
    parent_node: Optional[str] = None
    related_nodes: List[str] = []
    created_at: str
    updated_at: str

class NoteManager:
    def __init__(self):
        self.obsidian = ObsidianUtils()

    def create_note(self, title: str, content: str, metadata: NoteMetadata) -> str:
        """Create a new note with the given content and metadata."""
        try:
            note_path = self.obsidian.get_note_path(title)
            if note_path.exists():
                raise NoteAlreadyExistsError(f"Note {title} already exists")

            # Create frontmatter
            frontmatter = metadata.dict()
            
            # Combine frontmatter and content
            note_content = f"---\n{yaml.dump(frontmatter)}---\n\n{content}"
            
            # Write the note
            self.obsidian.write_note(str(note_path), note_content)
            return str(note_path)
        except Exception as e:
            raise NoteAlreadyExistsError(f"Error creating note {title}: {str(e)}")

    def update_note(self, title: str, content: Optional[str] = None, metadata: Optional[NoteMetadata] = None) -> None:
        """Update an existing note's content and/or metadata."""
        try:
            note_path = self.obsidian.get_note_path(title)
            if not note_path.exists():
                raise NoteNotFoundError(f"Note {title} not found")

            current_content = self.obsidian.read_note(str(note_path))
            current_frontmatter = self.obsidian.get_frontmatter(current_content)

            # Update frontmatter if provided
            if metadata:
                new_frontmatter = metadata.dict()
                current_frontmatter.update(new_frontmatter)
                current_content = self.obsidian.update_frontmatter(current_content, current_frontmatter)

            # Update content if provided
            if content:
                parts = current_content.split('---', 2)
                if len(parts) >= 3:
                    current_content = f"{parts[0]}---{parts[1]}---\n\n{content}"
                else:
                    current_content = content

            self.obsidian.write_note(str(note_path), current_content)
        except Exception as e:
            raise NoteNotFoundError(f"Error updating note {title}: {str(e)}")

    def delete_note(self, title: str) -> None:
        """Delete a note."""
        try:
            note_path = self.obsidian.get_note_path(title)
            if not note_path.exists():
                raise NoteNotFoundError(f"Note {title} not found")
            note_path.unlink()
        except Exception as e:
            raise NoteNotFoundError(f"Error deleting note {title}: {str(e)}")

    def get_note_metadata(self, title: str) -> NoteMetadata:
        """Get metadata for a note."""
        try:
            note_path = self.obsidian.get_note_path(title)
            if not note_path.exists():
                raise NoteNotFoundError(f"Note {title} not found")

            content = self.obsidian.read_note(str(note_path))
            frontmatter = self.obsidian.get_frontmatter(content)
            return NoteMetadata(**frontmatter)
        except Exception as e:
            raise NoteNotFoundError(f"Error getting metadata for note {title}: {str(e)}")

    def get_note_content(self, title: str) -> str:
        """Get content of a note."""
        try:
            note_path = self.obsidian.get_note_path(title)
            if not note_path.exists():
                raise NoteNotFoundError(f"Note {title} not found")

            content = self.obsidian.read_note(str(note_path))
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
            return content.strip()
        except Exception as e:
            raise NoteNotFoundError(f"Error getting content for note {title}: {str(e)}")

    def create_note_from_template(self, title: str, template_name: str, context: Dict) -> str:
        """Create a new note using a template."""
        try:
            # Render template
            content = self.obsidian.render_template(template_name, context)
            
            # Create metadata
            metadata = NoteMetadata(
                title=title,
                type=context.get("type", "note"),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Create note
            return self.create_note(title, content, metadata)
        except Exception as e:
            raise TemplateNotFoundError(f"Error creating note from template {template_name}: {str(e)}")

    def update_note_hierarchy(self, title: str, parent_node: Optional[str] = None, related_nodes: Optional[List[str]] = None) -> None:
        """Update a note's hierarchy information."""
        try:
            metadata = self.get_note_metadata(title)
            
            if parent_node is not None:
                metadata.parent_node = parent_node
            if related_nodes is not None:
                metadata.related_nodes = related_nodes
            
            self.update_note(title, metadata=metadata)
        except Exception as e:
            raise NoteNotFoundError(f"Error updating hierarchy for note {title}: {str(e)}") 
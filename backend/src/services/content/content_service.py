from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from datetime import datetime
import yaml
from pydantic import BaseModel, Field, ConfigDict
import jinja2

from ..base_service import BaseService
from ...core.exceptions import ContentManagementError

class NoteTemplate(BaseModel):
    """Model for note templates."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None

class NoteMetadata(BaseModel):
    """Model for note metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    title: str
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class ContentConfig(BaseModel):
    """Configuration for content management service."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    vault_path: Path
    templates_path: Path
    default_template: str = "default"
    enforce_templates: bool = True
    auto_update_frontmatter: bool = True

class ContentService(BaseService):
    """Service for managing content and notes in the Obsidian vault."""

    def _initialize(self) -> None:
        """Initialize content service configuration and resources."""
        self.config_model = ContentConfig(**self.config)
        self._templates: Dict[str, NoteTemplate] = {}
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.config_model.templates_path)),
            autoescape=True
        )
        self._ensure_directories()
        self._load_templates()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.config_model.vault_path.mkdir(parents=True, exist_ok=True)
        self.config_model.templates_path.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the content management service."""
        pass  # No background tasks needed

    async def stop(self) -> None:
        """Stop the content management service."""
        pass  # No cleanup needed

    async def health_check(self) -> bool:
        """Check if the content service is healthy."""
        return (
            self.config_model.vault_path.exists() and
            self.config_model.templates_path.exists() and
            bool(self._templates)
        )

    def _load_templates(self) -> None:
        """Load note templates from the templates directory."""
        for template_file in self.config_model.templates_path.glob("*.md"):
            try:
                content = template_file.read_text()
                frontmatter, template_content = self._parse_frontmatter(content)
                self._templates[template_file.stem] = NoteTemplate(
                    name=template_file.stem,
                    content=template_content,
                    **frontmatter
                )
            except Exception as e:
                raise ContentManagementError(f"Failed to load template {template_file}: {str(e)}")

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter or {}, parts[2].strip()
        except Exception as e:
            raise ContentManagementError(f"Failed to parse frontmatter: {str(e)}")

    async def create_note(
        self,
        title: str,
        content: str = "",
        template: Optional[str] = None,
        metadata: Optional[NoteMetadata] = None,
        path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Create a new note in the vault."""
        try:
            template_name = template or self.config_model.default_template
            if template_name not in self._templates:
                raise ContentManagementError(f"Template '{template_name}' not found")

            template_obj = self._templates[template_name]
            note_metadata = metadata or NoteMetadata(title=title)
            
            # Render template with context
            template = self._jinja_env.from_string(template_obj.content)
            rendered_content = template.render(
                title=title,
                content=content,
                metadata=note_metadata.dict(),
                date=datetime.now()
            )

            # Determine note path
            if path:
                note_path = Path(path)
            else:
                safe_title = self._safe_filename(title)
                note_path = self.config_model.vault_path / f"{safe_title}.md"

            # Ensure parent directory exists
            note_path.parent.mkdir(parents=True, exist_ok=True)

            # Write note content with frontmatter
            frontmatter = {
                **template_obj.frontmatter,
                **note_metadata.dict(exclude_none=True)
            }
            note_content = "---\n"
            note_content += yaml.dump(frontmatter, default_flow_style=False)
            note_content += "---\n\n"
            note_content += rendered_content

            note_path.write_text(note_content)
            return note_path

        except Exception as e:
            raise ContentManagementError(f"Failed to create note: {str(e)}")

    async def update_note(
        self,
        note_path: Union[str, Path],
        content: Optional[str] = None,
        metadata: Optional[NoteMetadata] = None
    ) -> None:
        """Update an existing note's content and/or metadata."""
        try:
            note_path = Path(note_path)
            if not note_path.exists():
                raise ContentManagementError(f"Note not found: {note_path}")

            current_content = note_path.read_text()
            current_frontmatter, current_content_body = self._parse_frontmatter(current_content)

            # Update frontmatter if provided
            if metadata:
                current_frontmatter.update(metadata.dict(exclude_none=True))
                current_frontmatter["modified"] = datetime.now()

            # Create updated note content
            new_content = "---\n"
            new_content += yaml.dump(current_frontmatter, default_flow_style=False)
            new_content += "---\n\n"
            new_content += content if content is not None else current_content_body

            note_path.write_text(new_content)

        except Exception as e:
            raise ContentManagementError(f"Failed to update note: {str(e)}")

    def _safe_filename(self, filename: str) -> str:
        """Convert a string to a safe filename."""
        # Replace invalid characters and spaces
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
        return safe_name.strip("_") 
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.exceptions import TemplateError
from ..base_service import BaseService

class TemplateMetadata(BaseModel):
    """Model for template metadata."""
    name: str
    description: Optional[str] = None
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    variables: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class TemplateManager(BaseService):
    """Service for managing note templates."""
    
    def __init__(self, settings):
        """Initialize the template manager.
        
        Args:
            settings: Application settings
        """
        super().__init__(settings)
        self.template_dir = Path(settings.TEMPLATE_DIR)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_template(
        self,
        name: str,
        content: str,
        metadata: Optional[TemplateMetadata] = None
    ) -> Dict[str, Any]:
        """Create a new template.
        
        Args:
            name: Template name
            content: Template content
            metadata: Optional template metadata
            
        Returns:
            Template information
        """
        try:
            path = self.template_dir / f"{name}.md"
            if path.exists():
                raise TemplateError(f"Template {name} already exists")
                
            if metadata is None:
                metadata = TemplateMetadata(name=name)
                
            # Extract variables from content
            variables = self._extract_variables(content)
            metadata.variables = variables
            
            # Write template
            path.write_text(content)
            
            return {
                "name": name,
                "path": str(path),
                "metadata": metadata.dict()
            }
        except Exception as e:
            raise TemplateError(f"Error creating template: {str(e)}")
            
    async def get_template(self, name: str) -> Dict[str, Any]:
        """Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template information
        """
        try:
            path = self.template_dir / f"{name}.md"
            if not path.exists():
                raise TemplateError(f"Template {name} does not exist")
                
            content = path.read_text()
            metadata = self._load_metadata(path)
            
            return {
                "name": name,
                "content": content,
                "metadata": metadata.dict()
            }
        except Exception as e:
            raise TemplateError(f"Error getting template: {str(e)}")
            
    async def update_template(
        self,
        name: str,
        content: Optional[str] = None,
        metadata: Optional[TemplateMetadata] = None
    ) -> Dict[str, Any]:
        """Update a template.
        
        Args:
            name: Template name
            content: Optional new content
            metadata: Optional new metadata
            
        Returns:
            Updated template information
        """
        try:
            path = self.template_dir / f"{name}.md"
            if not path.exists():
                raise TemplateError(f"Template {name} does not exist")
                
            current_metadata = self._load_metadata(path)
            
            if content is not None:
                # Update content and extract variables
                path.write_text(content)
                variables = self._extract_variables(content)
                current_metadata.variables = variables
                
            if metadata is not None:
                # Update metadata
                current_metadata = TemplateMetadata(
                    **{**current_metadata.dict(), **metadata.dict()}
                )
                
            current_metadata.modified = datetime.now()
            
            return {
                "name": name,
                "path": str(path),
                "metadata": current_metadata.dict()
            }
        except Exception as e:
            raise TemplateError(f"Error updating template: {str(e)}")
            
    async def delete_template(self, name: str) -> Dict[str, Any]:
        """Delete a template.
        
        Args:
            name: Template name
            
        Returns:
            Deleted template information
        """
        try:
            path = self.template_dir / f"{name}.md"
            if not path.exists():
                raise TemplateError(f"Template {name} does not exist")
                
            metadata = self._load_metadata(path)
            path.unlink()
            
            return {
                "name": name,
                "path": str(path),
                "metadata": metadata.dict()
            }
        except Exception as e:
            raise TemplateError(f"Error deleting template: {str(e)}")
            
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates.
        
        Returns:
            List of template information
        """
        try:
            templates = []
            for path in self.template_dir.glob("*.md"):
                name = path.stem
                metadata = self._load_metadata(path)
                templates.append({
                    "name": name,
                    "path": str(path),
                    "metadata": metadata.dict()
                })
            return templates
        except Exception as e:
            raise TemplateError(f"Error listing templates: {str(e)}")
            
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variables from template content.
        
        Args:
            content: Template content
            
        Returns:
            List of variable names
        """
        # Simple variable extraction using {{variable}} syntax
        import re
        pattern = r"\{\{([^}]+)\}\}"
        matches = re.findall(pattern, content)
        return list(set(matches))
        
    def _load_metadata(self, path: Path) -> TemplateMetadata:
        """Load template metadata.
        
        Args:
            path: Template path
            
        Returns:
            Template metadata
        """
        # For now, just create basic metadata
        # In the future, this could load from a metadata file
        return TemplateMetadata(
            name=path.stem,
            created=datetime.fromtimestamp(path.stat().st_ctime),
            modified=datetime.fromtimestamp(path.stat().st_mtime)
        ) 
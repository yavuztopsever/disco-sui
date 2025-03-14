from smolagents import Tool
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ToolResponse(BaseModel):
    """Base model for tool responses."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Optional[Any] = Field(None, description="The result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata about the execution")

class BaseTool(Tool):
    """Base class for all tools with common functionality."""
    
    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _ensure_path_exists(self, path: str) -> None:
        """Ensure a directory path exists."""
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create path {path}: {str(e)}")
            raise
        
    def _get_full_path(self, relative_path: str) -> str:
        """Get the full path for a given relative path."""
        return os.path.join(self.vault_path, relative_path)
        
    def _read_file(self, file_path: str) -> str:
        """Read content from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {str(e)}")
            raise Exception(f"Error reading file {file_path}: {str(e)}")
            
    def _write_file(self, file_path: str, content: str) -> None:
        """Write content to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to write to file {file_path}: {str(e)}")
            raise Exception(f"Error writing to file {file_path}: {str(e)}")
            
    def _list_files(self, directory: str, extension: str = '.md') -> List[str]:
        """List files with given extension in a directory."""
        try:
            files = []
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(extension):
                        rel_path = os.path.relpath(os.path.join(root, filename), self.vault_path)
                        files.append(rel_path)
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in {directory}: {str(e)}")
            raise Exception(f"Error listing files in {directory}: {str(e)}")
            
    def _get_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract frontmatter from markdown content."""
        try:
            if not content.startswith('---'):
                return {}
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}
                
            frontmatter = parts[1].strip()
            return json.loads(frontmatter)
        except Exception as e:
            raise Exception(f"Error parsing frontmatter: {str(e)}")
            
    def _update_frontmatter(self, content: str, frontmatter: Dict[str, Any]) -> str:
        """Update frontmatter in markdown content."""
        try:
            if not content.startswith('---'):
                return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n{content}"
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n{content}"
                
            return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n{parts[2]}"
        except Exception as e:
            raise Exception(f"Error updating frontmatter: {str(e)}")
            
    def _validate_path(self, path: str) -> bool:
        """Validate if a path is within the vault directory."""
        try:
            full_path = os.path.abspath(self._get_full_path(path))
            vault_path = os.path.abspath(self.vault_path)
            return full_path.startswith(vault_path)
        except Exception:
            return False 

    def _validate_inputs(self, inputs: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate required input fields."""
        missing_fields = [field for field in required_fields if field not in inputs]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def _format_response(self, success: bool, result: Any = None, error: str = None, metadata: Dict[str, Any] = None) -> ToolResponse:
        """Format a standardized tool response."""
        return ToolResponse(
            success=success,
            result=result,
            error=error,
            metadata=metadata or {}
        )

    def get_examples(self) -> List[Dict[str, Any]]:
        """Get example usage of the tool."""
        return getattr(self, 'examples', [])

    def get_documentation(self) -> Dict[str, Any]:
        """Get comprehensive documentation for the tool."""
        return {
            'name': self.name,
            'description': self.description,
            'inputs': self.inputs,
            'output_type': self.output_type,
            'examples': self.get_examples(),
            'error_handling': getattr(self, 'error_handling', {}),
            'dependencies': getattr(self, 'dependencies', [])
        }

class FrontmatterManagerTool(BaseTool):
    name = "frontmatter_manager"
    description = "Comprehensive YAML frontmatter management for Obsidian notes"
    inputs = {
        "action": {
            "type": "string",
            "description": "The action to perform",
            "enum": ["get", "update", "validate", "remove_field", "search", "add_metadata", "remove_metadata", "list_metadata"]
        },
        "path": {
            "type": "string",
            "description": "The path to the note (required for get, update, remove_field, add_metadata, remove_metadata)",
            "nullable": True
        },
        "content": {
            "type": "string",
            "description": "The note content (required for get, update)",
            "nullable": True
        },
        "frontmatter": {
            "type": "object",
            "description": "The frontmatter to update (required for update)",
            "nullable": True
        },
        "schema": {
            "type": "object",
            "description": "The schema to validate against (required for validate)",
            "nullable": True
        },
        "field": {
            "type": "string",
            "description": "The field to remove (required for remove_field)",
            "nullable": True
        },
        "search_field": {
            "type": "string",
            "description": "The field to search by (required for search)",
            "nullable": True
        },
        "search_value": {
            "type": "any",
            "description": "The value to search for (required for search)",
            "nullable": True
        },
        "metadata": {
            "type": "string",
            "description": "The metadata to add/remove (required for add_metadata, remove_metadata)",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, action: str, **kwargs) -> Dict[str, Any]:
        try:
            if action == "get":
                if not kwargs.get("content"):
                    raise ValueError("Content is required for get action")
                return self.get_frontmatter(kwargs["content"])
            elif action == "update":
                if not kwargs.get("content") or not kwargs.get("frontmatter"):
                    raise ValueError("Content and frontmatter are required for update action")
                return self.update_frontmatter(kwargs["content"], kwargs["frontmatter"])
            elif action == "validate":
                if not kwargs.get("frontmatter") or not kwargs.get("schema"):
                    raise ValueError("Frontmatter and schema are required for validate action")
                return self.validate_frontmatter(kwargs["frontmatter"], kwargs["schema"])
            elif action == "remove_field":
                if not kwargs.get("content") or not kwargs.get("field"):
                    raise ValueError("Content and field are required for remove_field action")
                return self.remove_field(kwargs["content"], kwargs["field"])
            elif action == "search":
                if not kwargs.get("search_field") or not kwargs.get("search_value"):
                    raise ValueError("Search field and value are required for search action")
                return self.search_by_field(kwargs["search_field"], kwargs["search_value"])
            elif action == "add_metadata":
                if not kwargs.get("path") or not kwargs.get("metadata"):
                    raise ValueError("Path and metadata are required for add_metadata action")
                return self.add_metadata(kwargs["path"], kwargs["metadata"])
            elif action == "remove_metadata":
                if not kwargs.get("path") or not kwargs.get("metadata"):
                    raise ValueError("Path and metadata are required for remove_metadata action")
                return self.remove_metadata(kwargs["path"], kwargs["metadata"])
            elif action == "list_metadata":
                return self.list_metadata()
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            return {"error": str(e)}

    def get_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract frontmatter from markdown content."""
        try:
            if not content.startswith('---'):
                return {}
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}
                
            frontmatter = parts[1].strip()
            return json.loads(frontmatter)
        except Exception as e:
            raise Exception(f"Error parsing frontmatter: {str(e)}")
            
    def update_frontmatter(self, content: str, frontmatter: Dict[str, Any]) -> str:
        """Update frontmatter in markdown content."""
        try:
            if not content.startswith('---'):
                return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n{content}"
            
            parts = content.split('---', 2)
            if len(parts) < 3:
                return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n\n{content}"
                
            return f"---\n{json.dumps(frontmatter, indent=2)}\n---\n{parts[2]}"
        except Exception as e:
            raise Exception(f"Error updating frontmatter: {str(e)}")
            
    def validate_frontmatter(self, frontmatter: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate frontmatter against a schema."""
        try:
            # TODO: Implement schema validation
            return True
        except Exception as e:
            raise Exception(f"Error validating frontmatter: {str(e)}")
            
    def remove_field(self, content: str, field: str) -> str:
        """Remove a field from frontmatter."""
        try:
            frontmatter = self.get_frontmatter(content)
            if field in frontmatter:
                del frontmatter[field]
            return self.update_frontmatter(content, frontmatter)
        except Exception as e:
            raise Exception(f"Error removing field from frontmatter: {str(e)}")
            
    def search_by_field(self, field: str, value: Any) -> List[str]:
        """Search notes by frontmatter field value."""
        try:
            matching_notes = []
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.get_frontmatter(content)
                if field in frontmatter and frontmatter[field] == value:
                    matching_notes.append(file_path)
            return matching_notes
        except Exception as e:
            raise Exception(f"Error searching by frontmatter field: {str(e)}")

    def add_metadata(self, path: str, metadata: str) -> Dict[str, Any]:
        """Add metadata to a note."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.get_frontmatter(content)
            
            if 'metadata' not in frontmatter:
                frontmatter['metadata'] = []
            
            if metadata not in frontmatter['metadata']:
                frontmatter['metadata'].append(metadata)
            
            updated_content = self.update_frontmatter(content, frontmatter)
            self._write_file(file_path, updated_content)
            return {"success": True, "message": f"Metadata '{metadata}' added to note '{path}' successfully"}
        except Exception as e:
            return {"error": str(e)}

    def remove_metadata(self, path: str, metadata: str) -> Dict[str, Any]:
        """Remove metadata from a note."""
        try:
            file_path = self._get_full_path(path)
            content = self._read_file(file_path)
            frontmatter = self.get_frontmatter(content)
            
            if 'metadata' in frontmatter and metadata in frontmatter['metadata']:
                frontmatter['metadata'].remove(metadata)
                updated_content = self.update_frontmatter(content, frontmatter)
                self._write_file(file_path, updated_content)
                return {"success": True, "message": f"Metadata '{metadata}' removed from note '{path}' successfully"}
            else:
                return {"error": f"Metadata '{metadata}' not found in note '{path}'"}
        except Exception as e:
            return {"error": str(e)}

    def list_metadata(self) -> List[str]:
        """List all metadata in the vault."""
        try:
            metadata_set = set()
            for file_path in self._list_files(self.vault_path):
                content = self._read_file(file_path)
                frontmatter = self.get_frontmatter(content)
                if 'metadata' in frontmatter:
                    metadata_set.update(frontmatter['metadata'])
            return list(metadata_set)
        except Exception as e:
            return {"error": str(e)} 
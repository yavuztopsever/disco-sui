from smolagents import Tool
from typing import Dict, Any, Optional, List, Type, Union, Callable, Awaitable
from pydantic import BaseModel, Field
import os
import json
from pathlib import Path
import logging
import asyncio
from src.core.exceptions import (
    DiscoSuiError,
    FileSystemError,
    ValidationError,
    ResourceNotFoundError,
    NoteNotFoundError,
    FrontmatterError,
    ToolError
)
from datetime import datetime
import yaml
import jsonschema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ToolResponse(BaseModel):
    """Base model for tool responses."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Optional[Any] = Field(None, description="The result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata about the execution")
    execution_time: Optional[float] = Field(None, description="Time taken to execute the tool in seconds")

class BaseTool(Tool):
    """Base class for all DiscoSui tools following smolagents Tool interface."""
    
    def __init__(self):
        """Initialize the base tool."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the given parameters.
        
        This method follows the smolagents Tool interface for execution.
        
        Args:
            parameters (Dict[str, Any]): The parameters for tool execution
            
        Returns:
            Dict[str, Any]: The execution result
            
        Raises:
            ToolError: If tool execution fails
        """
        try:
            # Validate parameters
            self._validate_parameters(parameters)
            
            # Execute tool-specific logic
            result = await self._execute_tool(parameters)
            
            # Format response
            return self._format_response(result)
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {str(e)}")
            return self._format_error(str(e))
            
    def _validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate input parameters against tool schema.
        
        Args:
            parameters (Dict[str, Any]): Parameters to validate
            
        Raises:
            ValidationError: If parameters are invalid
        """
        try:
            # Get tool schema
            schema = self.get_schema()
            
            # Check required parameters
            for param_name, param_info in schema["inputs"].items():
                if param_info.get("required", False) and param_name not in parameters:
                    raise ValidationError(f"Missing required parameter: {param_name}")
                    
            # Validate parameter types
            for param_name, param_value in parameters.items():
                if param_name in schema["inputs"]:
                    param_info = schema["inputs"][param_name]
                    if not self._validate_parameter_type(param_value, param_info["type"]):
                        raise ValidationError(
                            f"Invalid type for parameter {param_name}. "
                            f"Expected {param_info['type']}, got {type(param_value)}"
                        )
                        
        except Exception as e:
            raise ValidationError(f"Parameter validation failed: {str(e)}")
            
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate a parameter's type.
        
        Args:
            value (Any): The value to validate
            expected_type (str): The expected type
            
        Returns:
            bool: Whether the type is valid
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type not in type_map:
            return True  # Skip validation for unknown types
            
        expected_python_type = type_map[expected_type]
        return isinstance(value, expected_python_type)
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute tool-specific logic.
        
        This method should be overridden by tool implementations.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The tool execution result
            
        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplementedError("Tool implementation must override _execute_tool method")
        
    def _format_response(self, result: Any) -> Dict[str, Any]:
        """Format the tool execution result.
        
        Args:
            result (Any): The raw execution result
            
        Returns:
            Dict[str, Any]: The formatted response
        """
        return {
            "success": True,
            "result": result,
            "metadata": {
                "tool_name": self.name,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    def _format_error(self, error: str) -> Dict[str, Any]:
        """Format an error response.
        
        Args:
            error (str): The error message
            
        Returns:
            Dict[str, Any]: The formatted error response
        """
        return {
            "success": False,
            "error": error,
            "metadata": {
                "tool_name": self.name,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema.
        
        This method follows the smolagents Tool interface for schema definition.
        
        Returns:
            Dict[str, Any]: The tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "output_type": self.output_type
        }
        
    @property
    def name(self) -> str:
        """Get the tool's name.
        
        Returns:
            str: The tool name
        """
        raise NotImplementedError("Tool implementation must define name property")
        
    @property
    def description(self) -> str:
        """Get the tool's description.
        
        Returns:
            str: The tool description
        """
        raise NotImplementedError("Tool implementation must define description property")
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool's input schema.
        
        Returns:
            Dict[str, Any]: The input schema
        """
        raise NotImplementedError("Tool implementation must define inputs property")
        
    @property
    def output_type(self) -> str:
        """Get the tool's output type.
        
        Returns:
            str: The output type
        """
        raise NotImplementedError("Tool implementation must define output_type property")

class FrontmatterManagerTool(BaseTool):
    """Frontmatter management tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the frontmatter manager tool."""
        super().__init__()
        self.vault_path = vault_path
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "frontmatter_manager"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Comprehensive YAML frontmatter management for Obsidian notes"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["get", "update", "validate", "remove_field", "search", "add_metadata", "remove_metadata", "list_metadata"],
                "required": True
            },
            "path": {
                "type": "string",
                "description": "The path to the note (required for get, update, remove_field, add_metadata, remove_metadata)",
                "required": False
            },
            "content": {
                "type": "string",
                "description": "The note content (required for get, update)",
                "required": False
            },
            "frontmatter": {
                "type": "object",
                "description": "The frontmatter to update (required for update)",
                "required": False
            },
            "schema": {
                "type": "object",
                "description": "The schema to validate against (required for validate)",
                "required": False
            },
            "field": {
                "type": "string",
                "description": "The field to remove (required for remove_field)",
                "required": False
            },
            "search_field": {
                "type": "string",
                "description": "The field to search by (required for search)",
                "required": False
            },
            "search_value": {
                "type": "any",
                "description": "The value to search for (required for search)",
                "required": False
            },
            "metadata": {
                "type": "string",
                "description": "The metadata to add/remove (required for add_metadata, remove_metadata)",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the frontmatter management operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        
        try:
            # Execute requested action
            if action == "get":
                return await self._get_frontmatter(parameters)
            elif action == "update":
                return await self._update_frontmatter(parameters)
            elif action == "validate":
                return await self._validate_frontmatter(parameters)
            elif action == "remove_field":
                return await self._remove_field(parameters)
            elif action == "search":
                return await self._search_by_field(parameters)
            elif action == "add_metadata":
                return await self._add_metadata(parameters)
            elif action == "remove_metadata":
                return await self._remove_metadata(parameters)
            elif action == "list_metadata":
                return await self._list_metadata()
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Frontmatter operation failed: {str(e)}")
            raise
            
    async def _get_frontmatter(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get frontmatter from content."""
        content = parameters.get("content")
        if not content:
            raise ValueError("Content is required for get operation")
            
        if not content.startswith('---'):
            return {
                "frontmatter": {},
                "timestamp": datetime.now().isoformat()
            }
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {
                "frontmatter": {},
                "timestamp": datetime.now().isoformat()
            }
            
        try:
            frontmatter = yaml.safe_load(parts[1].strip())
            return {
                "frontmatter": frontmatter,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error parsing frontmatter: {str(e)}")
            
    async def _update_frontmatter(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update frontmatter in content."""
        content = parameters.get("content")
        frontmatter = parameters.get("frontmatter")
        
        if not content or frontmatter is None:
            raise ValueError("Content and frontmatter are required for update operation")
            
        try:
            if not content.startswith('---'):
                updated_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{content}"
            else:
                parts = content.split('---', 2)
                if len(parts) < 3:
                    updated_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{content}"
                else:
                    updated_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{parts[2]}"
                    
            return {
                "content": updated_content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error updating frontmatter: {str(e)}")
            
    async def _validate_frontmatter(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate frontmatter against schema."""
        frontmatter = parameters.get("frontmatter")
        schema = parameters.get("schema")
        
        if frontmatter is None or schema is None:
            raise ValueError("Frontmatter and schema are required for validate operation")
            
        try:
            validator = jsonschema.Draft7Validator(schema)
            errors = sorted(validator.iter_errors(frontmatter), key=lambda e: e.path)
            
            return {
                "is_valid": len(errors) == 0,
                "errors": [str(error) for error in errors],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error validating frontmatter: {str(e)}")
            
    async def _remove_field(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove field from frontmatter."""
        content = parameters.get("content")
        field = parameters.get("field")
        
        if not content or not field:
            raise ValueError("Content and field are required for remove_field operation")
            
        try:
            frontmatter_result = await self._get_frontmatter({"content": content})
            frontmatter = frontmatter_result["frontmatter"]
            
            if field in frontmatter:
                del frontmatter[field]
                update_result = await self._update_frontmatter({
                    "content": content,
                    "frontmatter": frontmatter
                })
                return {
                    "content": update_result["content"],
                    "removed_field": field,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "content": content,
                    "message": f"Field {field} not found in frontmatter",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            raise FrontmatterError(f"Error removing field from frontmatter: {str(e)}")
            
    async def _search_by_field(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes by frontmatter field."""
        search_field = parameters.get("search_field")
        search_value = parameters.get("search_value")
        
        if not search_field or search_value is None:
            raise ValueError("Search field and value are required for search operation")
            
        try:
            matching_notes = []
            for file_path in Path(self.vault_path).rglob("*.md"):
                content = file_path.read_text()
                frontmatter_result = await self._get_frontmatter({"content": content})
                frontmatter = frontmatter_result["frontmatter"]
                
                if search_field in frontmatter and frontmatter[search_field] == search_value:
                    matching_notes.append(str(file_path.relative_to(self.vault_path)))
                    
            return {
                "matches": matching_notes,
                "count": len(matching_notes),
                "search_field": search_field,
                "search_value": search_value,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error searching by frontmatter field: {str(e)}")
            
    async def _add_metadata(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata to note."""
        path = parameters.get("path")
        metadata = parameters.get("metadata")
        
        if not path or not metadata:
            raise ValueError("Path and metadata are required for add_metadata operation")
            
        try:
            file_path = Path(self.vault_path) / path
            content = file_path.read_text()
            
            frontmatter_result = await self._get_frontmatter({"content": content})
            frontmatter = frontmatter_result["frontmatter"]
            
            if "metadata" not in frontmatter:
                frontmatter["metadata"] = []
                
            if metadata not in frontmatter["metadata"]:
                frontmatter["metadata"].append(metadata)
                update_result = await self._update_frontmatter({
                    "content": content,
                    "frontmatter": frontmatter
                })
                file_path.write_text(update_result["content"])
                
            return {
                "message": f"Added metadata {metadata} to {path}",
                "path": path,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error adding metadata: {str(e)}")
            
    async def _remove_metadata(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove metadata from note."""
        path = parameters.get("path")
        metadata = parameters.get("metadata")
        
        if not path or not metadata:
            raise ValueError("Path and metadata are required for remove_metadata operation")
            
        try:
            file_path = Path(self.vault_path) / path
            content = file_path.read_text()
            
            frontmatter_result = await self._get_frontmatter({"content": content})
            frontmatter = frontmatter_result["frontmatter"]
            
            if "metadata" in frontmatter and metadata in frontmatter["metadata"]:
                frontmatter["metadata"].remove(metadata)
                update_result = await self._update_frontmatter({
                    "content": content,
                    "frontmatter": frontmatter
                })
                file_path.write_text(update_result["content"])
                
            return {
                "message": f"Removed metadata {metadata} from {path}",
                "path": path,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error removing metadata: {str(e)}")
            
    async def _list_metadata(self) -> Dict[str, Any]:
        """List all metadata in vault."""
        try:
            metadata_set = set()
            for file_path in Path(self.vault_path).rglob("*.md"):
                content = file_path.read_text()
                frontmatter_result = await self._get_frontmatter({"content": content})
                frontmatter = frontmatter_result["frontmatter"]
                
                if "metadata" in frontmatter:
                    metadata_set.update(frontmatter["metadata"])
                    
            return {
                "metadata": list(metadata_set),
                "count": len(metadata_set),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise FrontmatterError(f"Error listing metadata: {str(e)}") 
from typing import Dict, Any, Optional, List
from .base_tools import BaseTool, FrontmatterManagerTool
from ..services.organization.tags import TagManager, TagValidator
import re
import asyncio
from smolagents import Tool
from pathlib import Path
from datetime import datetime

from ..core.tool_interfaces import TagTool

class TagTool(BaseTool):
    """Tool for tag management operations.
    
    This implements the TagTool functionality from Flow 7.
    """
    
    def __init__(self, vault_path: str):
        """Initialize the tag tool.
        
        Args:
            vault_path: Path to the Obsidian vault
        """
        super().__init__()
        self.vault_path = vault_path
        self.tag_manager = TagManager(vault_path)
        self.tag_validator = TagValidator()
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "TagTool"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Manage tags for Obsidian notes"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["add", "remove", "validate", "list", "search", "suggest"],
                "required": True
            },
            "tag": {
                "type": "string",
                "description": "The tag to add/remove/validate",
                "required": False
            },
            "path": {
                "type": "string",
                "description": "Path to the note for add/remove operations",
                "required": False
            },
            "content": {
                "type": "string",
                "description": "Content to analyze for tag suggestions",
                "required": False
            }
        }
        
    def get_manifest(self) -> Dict[str, Any]:
        """Get the tool manifest for LLM agent.
        
        Returns:
            Dict[str, Any]: Tool manifest with schema and examples
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.inputs,
            "examples": [
                {
                    "action": "add",
                    "tag": "#project/website",
                    "path": "/path/to/note.md"
                },
                {
                    "action": "validate",
                    "tag": "#meeting/client"
                },
                {
                    "action": "suggest",
                    "content": "Meeting with marketing team about the new website launch campaign."
                }
            ]
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tag management operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        
        try:
            # Initialize services if needed
            if not self.tag_validator.is_running:
                await self.tag_validator.start()
            if not self.tag_manager.is_running:
                await self.tag_manager.start()
                
            # Execute requested action based on Flow 7 (Tag Management Flow)
            if action == "add":
                return await self._add_tag(parameters)
            elif action == "remove":
                return await self._remove_tag(parameters)
            elif action == "validate":
                return await self._validate_tag(parameters)
            elif action == "list":
                return await self._list_tags()
            elif action == "search":
                return await self._search_tags(parameters)
            elif action == "suggest":
                return await self._suggest_tags(parameters)
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Tag operation failed: {str(e)}")
            raise
            
    async def _add_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add a tag to a note.
        
        This implements the "Add Tag" operation in Flow 7.
        """
        path = parameters.get("path")
        tag = parameters.get("tag")
        if not path or not tag:
            raise ValueError("Path and tag are required for add operation")
            
        # First validate the tag
        validation_result = await self.tag_validator.validate_tag(tag)
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "message": f"Invalid tag: {validation_result['error']}",
                "tag": tag
            }
            
        # Add the tag to the note
        await self.tag_manager.add_tag(path, tag)
        
        # Return success following the Flow 7 format
        return {
            "operation_result": "success",
            "path": path,
            "tag": tag
        }
        
    async def _remove_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a tag from a note.
        
        This implements the "Remove Tag" operation in Flow 7.
        """
        path = parameters.get("path")
        tag = parameters.get("tag")
        if not path or not tag:
            raise ValueError("Path and tag are required for remove operation")
            
        # Check tag existence in the note
        note_tags = await self.tag_manager.get_note_tags(path)
        if tag not in note_tags:
            return {
                "success": False,
                "message": f"Tag {tag} not found in note {path}",
                "tag": tag,
                "path": path
            }
            
        # Remove the tag
        await self.tag_manager.remove_tag(path, tag)
        
        # Return success following the Flow 7 format
        return {
            "operation_result": "success",
            "path": path,
            "tag": tag
        }
        
    async def _validate_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a tag.
        
        This implements the "Validate Tag" operation in Flow 7.
        """
        tag = parameters.get("tag")
        if not tag:
            raise ValueError("Tag is required for validate operation")
            
        # Validate the tag using the tag validator
        validation_result = await self.tag_validator.validate_tag(tag)
        
        return {
            "tag": tag,
            "is_valid": validation_result["is_valid"],
            "validation_result": validation_result
        }
        
    async def _list_tags(self) -> Dict[str, Any]:
        """List all tags in the vault.
        
        This corresponds to getting all tags in Flow 7.
        """
        tags = await self.tag_manager.list_tags()
        
        # Format according to Flow 7
        return {
            "tags": tags,
            "count": len(tags)
        }
        
    async def _search_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for tags matching a pattern.
        
        This corresponds to the search functionality in Flow 7.
        """
        tag = parameters.get("tag")
        if not tag:
            raise ValueError("Tag pattern is required for search operation")
            
        matches = await self.tag_manager.search_tags(tag)
        
        # Format according to Flow 7
        return {
            "matches": matches,
            "count": len(matches),
            "pattern": tag
        }
        
    async def _suggest_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest tags based on content.
        
        This corresponds to the tag suggestion functionality in Flow 7.
        """
        content = parameters.get("content")
        path = parameters.get("path")
        
        # If path is provided, get content from the note
        if not content and path:
            content = await self._get_note_content(path)
            
        if not content:
            raise ValueError("Either content or path must be provided for suggest operation")
            
        # Use the tag manager to suggest tags based on content
        suggestions = await self.tag_manager.suggest_tags_from_content(content)
        
        # Format according to Flow 7
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    async def _get_note_content(self, path: str) -> str:
        """Helper method to get note content."""
        try:
            note_path = Path(self.vault_path) / path
            if not note_path.exists():
                raise FileNotFoundError(f"Note not found: {path}")
                
            return note_path.read_text()
        except Exception as e:
            raise ValueError(f"Failed to read note content: {str(e)}")

class ExtractTagsTool(BaseTool):
    """Tool for extracting tags from content."""
    
    def __init__(self, vault_path: str):
        """Initialize the tool."""
        super().__init__()
        self.vault_path = vault_path
        self.tag_tool_interface = None  # This would be initialized with the proper interface
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "extract_tags"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Extract tags from content"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool."""
        content = parameters.get("content", "")
        include_hierarchy = parameters.get("include_hierarchy", True)
        
        # This would call the actual implementation
        if self.tag_tool_interface:
            return await self.tag_tool_interface.extract_tags(content, include_hierarchy)
        return []

class UpdateTagsTool(BaseTool):
    """Tool for updating tags in content."""
    
    def __init__(self, vault_path: str):
        """Initialize the tool."""
        super().__init__()
        self.vault_path = vault_path
        self.tag_tool_interface = None  # This would be initialized with the proper interface
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "update_tags"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Update tags in a file"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool."""
        path = parameters.get("path", "")
        tags = parameters.get("tags", [])
        operation = parameters.get("operation", "add")
        
        # This would call the actual implementation
        if self.tag_tool_interface:
            return await self.tag_tool_interface.update_tags(Path(path), tags, operation)
        return {}

class TagHierarchyTool(BaseTool):
    """Tool for managing tag hierarchies."""
    
    def __init__(self, vault_path: str):
        """Initialize the tool."""
        super().__init__()
        self.vault_path = vault_path
        self.tag_tool_interface = None  # This would be initialized with the proper interface
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "tag_hierarchy"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Analyze tag hierarchy"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool."""
        content = parameters.get("content", "")
        analysis_type = parameters.get("analysis_type", "tags")
        
        # This would call the actual implementation
        if self.tag_tool_interface:
            return await self.tag_tool_interface.analyze_content(content, analysis_type=analysis_type)
        return {} 
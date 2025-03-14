from typing import Dict, Any, Optional, List
from .base_tools import BaseTool, FrontmatterManagerTool
from ..services.organization.tags import TagManager, TagValidator
import re
import asyncio
from smolagents import Tool
from pathlib import Path
from datetime import datetime

from ..core.tool_interfaces import TagTool

class TagManagerTool(BaseTool):
    """Comprehensive tag management tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the tag manager tool."""
        super().__init__()
        self.vault_path = vault_path
        self.frontmatter_manager = FrontmatterManagerTool()
        self.tag_validator = TagValidator()
        self.tag_manager = TagManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "tag_manager"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Comprehensive tag management for Obsidian notes"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["add", "remove", "list", "search", "get_note_tags", "get_related", "suggest", "get_stats"],
                "required": True
            },
            "path": {
                "type": "string",
                "description": "The path to the note (required for add, remove, get_note_tags)",
                "required": False
            },
            "tag": {
                "type": "string",
                "description": "The tag to add/remove/search (required for add, remove, search, get_related)",
                "required": False
            },
            "tag_type": {
                "type": "string",
                "description": "The type of tag (concept, place, brand, company, service)",
                "enum": ["concept", "place", "brand", "company", "service"],
                "required": False
            },
            "max_suggestions": {
                "type": "integer",
                "description": "Maximum number of tag suggestions to return",
                "default": 5,
                "required": False
            }
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
                
            # Execute requested action
            if action == "add":
                return await self._add_tag(parameters)
            elif action == "remove":
                return await self._remove_tag(parameters)
            elif action == "list":
                return await self._list_tags()
            elif action == "search":
                return await self._search_tags(parameters)
            elif action == "get_note_tags":
                return await self._get_note_tags(parameters)
            elif action == "get_related":
                return await self._get_related_tags(parameters)
            elif action == "suggest":
                return await self._suggest_tags(parameters)
            elif action == "get_stats":
                return await self._get_tag_stats()
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Tag operation failed: {str(e)}")
            raise
            
    async def _add_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add a tag to a note."""
        path = parameters.get("path")
        tag = parameters.get("tag")
        if not path or not tag:
            raise ValueError("Path and tag are required for add operation")
            
        await self.tag_manager.add_tag(path, tag)
        return {
            "message": f"Added tag {tag} to {path}",
            "path": path,
            "tag": tag,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _remove_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a tag from a note."""
        path = parameters.get("path")
        tag = parameters.get("tag")
        if not path or not tag:
            raise ValueError("Path and tag are required for remove operation")
            
        await self.tag_manager.remove_tag(path, tag)
        return {
            "message": f"Removed tag {tag} from {path}",
            "path": path,
            "tag": tag,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _list_tags(self) -> Dict[str, Any]:
        """List all tags in the vault."""
        tags = await self.tag_manager.list_tags()
        return {
            "tags": tags,
            "count": len(tags),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _search_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for tags matching a pattern."""
        tag = parameters.get("tag")
        if not tag:
            raise ValueError("Tag pattern is required for search operation")
            
        matches = await self.tag_manager.search_tags(tag)
        return {
            "matches": matches,
            "count": len(matches),
            "pattern": tag,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_note_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get tags for a specific note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for get_note_tags operation")
            
        tags = await self.tag_manager.get_note_tags(path)
        return {
            "path": path,
            "tags": tags,
            "count": len(tags),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_related_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get tags related to a given tag."""
        tag = parameters.get("tag")
        if not tag:
            raise ValueError("Tag is required for get_related operation")
            
        related = await self.tag_manager.get_related_tags(tag)
        return {
            "tag": tag,
            "related_tags": related,
            "count": len(related),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _suggest_tags(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest tags based on content."""
        path = parameters.get("path")
        max_suggestions = parameters.get("max_suggestions", 5)
        tag_type = parameters.get("tag_type")
        
        if not path:
            raise ValueError("Path is required for suggest operation")
            
        suggestions = await self.tag_manager.suggest_tags(
            path,
            max_suggestions=max_suggestions,
            tag_type=tag_type
        )
        return {
            "path": path,
            "suggestions": suggestions,
            "count": len(suggestions),
            "tag_type": tag_type,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_tag_stats(self) -> Dict[str, Any]:
        """Get tag usage statistics."""
        stats = await self.tag_manager.get_stats()
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

class ExtractTagsTool(TagTool):
    """Tool for extracting tags from content."""
    
    async def forward(
        self,
        content: str,
        include_hierarchy: bool = True
    ) -> List[str]:
        """Extract tags from content.
        
        Args:
            content: Content to extract tags from
            include_hierarchy: Whether to include hierarchical tags
            
        Returns:
            List of extracted tags
        """
        return await self.extract_tags(content, include_hierarchy)

class UpdateTagsTool(TagTool):
    """Tool for updating tags in content."""
    
    async def forward(
        self,
        path: Path,
        tags: List[str],
        operation: str = "add"
    ) -> Dict[str, Any]:
        """Update tags in a file.
        
        Args:
            path: Path to the file
            tags: Tags to update
            operation: Operation to perform ("add", "remove", "set")
            
        Returns:
            Update results
        """
        return await self.update_tags(path, tags, operation)

class TagHierarchyTool(TagTool):
    """Tool for managing tag hierarchies."""
    
    async def forward(
        self,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze tag hierarchy.
        
        Args:
            content: Content to analyze
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        return await self.analyze_content(content, analysis_type="tags", **kwargs) 
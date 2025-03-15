from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
from ..services.content.notes import NoteManager
from ..services.organization.folders import FolderManager
from pathlib import Path
from datetime import datetime
import asyncio
from smolagents import Tool

class NoteManagerTool(BaseTool):
    """Note management tool following smolagents Tool interface."""
    
    def __init__(self, vault_path: str):
        """Initialize the note manager tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        self.folder_manager = FolderManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "note_manager"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Comprehensive note management for Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["create", "update", "delete", "move", "list", "search", "get_content", "get_metadata"],
                "required": True
            },
            "path": {
                "type": "string",
                "description": "The path to the note",
                "required": False
            },
            "new_path": {
                "type": "string",
                "description": "The new path for move operations",
                "required": False
            },
            "content": {
                "type": "string",
                "description": "The content for create/update operations",
                "required": False
            },
            "metadata": {
                "type": "object",
                "description": "Metadata for the note",
                "required": False
            },
            "search_query": {
                "type": "string",
                "description": "Query for search operations",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the note management operation.
        
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
            if not self.note_manager.is_running:
                await self.note_manager.start()
            if not self.folder_manager.is_running:
                await self.folder_manager.start()
                
            # Execute requested action
            if action == "create":
                return await self._create_note(parameters)
            elif action == "update":
                return await self._update_note(parameters)
            elif action == "delete":
                return await self._delete_note(parameters)
            elif action == "move":
                return await self._move_note(parameters)
            elif action == "list":
                return await self._list_notes()
            elif action == "search":
                return await self._search_notes(parameters)
            elif action == "get_content":
                return await self._get_note_content(parameters)
            elif action == "get_metadata":
                return await self._get_note_metadata(parameters)
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Note operation failed: {str(e)}")
            raise
            
    async def _create_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new note."""
        path = parameters.get("path")
        content = parameters.get("content", "")
        metadata = parameters.get("metadata", {})
        
        if not path:
            raise ValueError("Path is required for create operation")
            
        await self.note_manager.create_note(path, content, metadata)
        return {
            "message": f"Created note at {path}",
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _update_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing note."""
        path = parameters.get("path")
        content = parameters.get("content")
        metadata = parameters.get("metadata")
        
        if not path:
            raise ValueError("Path is required for update operation")
            
        if content is not None:
            await self.note_manager.update_content(path, content)
        if metadata is not None:
            await self.note_manager.update_metadata(path, metadata)
            
        return {
            "message": f"Updated note at {path}",
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _delete_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for delete operation")
            
        await self.note_manager.delete_note(path)
        return {
            "message": f"Deleted note at {path}",
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _move_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Move a note to a new location."""
        path = parameters.get("path")
        new_path = parameters.get("new_path")
        
        if not path or not new_path:
            raise ValueError("Path and new_path are required for move operation")
            
        await self.note_manager.move_note(path, new_path)
        return {
            "message": f"Moved note from {path} to {new_path}",
            "old_path": path,
            "new_path": new_path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _list_notes(self) -> Dict[str, Any]:
        """List all notes in the vault."""
        notes = await self.note_manager.list_notes()
        return {
            "notes": notes,
            "count": len(notes),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _search_notes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for notes matching a query."""
        query = parameters.get("search_query")
        if not query:
            raise ValueError("Search query is required for search operation")
            
        results = await self.note_manager.search_notes(query)
        return {
            "results": results,
            "count": len(results),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_note_content(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get the content of a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for get_content operation")
            
        content = await self.note_manager.get_content(path)
        return {
            "path": path,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_note_metadata(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get the metadata of a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for get_metadata operation")
            
        metadata = await self.note_manager.get_metadata(path)
        return {
            "path": path,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

class CreateNoteTool(BaseTool):
    """Tool for creating notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the create note tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "create_note"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Create a new note in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "title": {
                "type": "string",
                "description": "The title of the note",
                "required": True
            },
            "content": {
                "type": "string",
                "description": "The content of the note",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "The folder to create the note in",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the create note operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        title = parameters["title"]
        content = parameters["content"]
        folder = parameters.get("folder")
        
        try:
            note_path = await self.note_manager.create_note(title, content, folder)
            return {
                "message": f"Created note {title}",
                "path": str(note_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to create note: {str(e)}")
            raise

class UpdateNoteTool(BaseTool):
    """Tool for updating notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the update note tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "update_note"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Update an existing note in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "title": {
                "type": "string",
                "description": "The title of the note",
                "required": True
            },
            "content": {
                "type": "string",
                "description": "The new content of the note",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "The folder containing the note",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the update note operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        title = parameters["title"]
        content = parameters["content"]
        folder = parameters.get("folder")
        
        try:
            success = await self.note_manager.update_note(title, content, folder)
            if success:
                return {
                    "message": f"Updated note {title}",
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "message": f"Note {title} not found",
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Failed to update note: {str(e)}")
            raise

class DeleteNoteTool(BaseTool):
    """Tool for deleting notes from the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the delete note tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "delete_note"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Delete a note from the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "title": {
                "type": "string",
                "description": "The title of the note",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "The folder containing the note",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the delete note operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        title = parameters["title"]
        folder = parameters.get("folder")
        
        try:
            success = await self.note_manager.delete_note(title, folder)
            if success:
                return {
                    "message": f"Deleted note {title}",
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "message": f"Note {title} not found",
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Failed to delete note: {str(e)}")
            raise

class ListNotesTool(BaseTool):
    """Tool for listing notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the list notes tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "list_notes"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "List notes in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "folder": {
                "type": "string",
                "description": "The folder to list notes from",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the list notes operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        folder = parameters.get("folder")
        
        try:
            notes = await self.note_manager.list_notes(folder)
            return {
                "notes": notes,
                "count": len(notes),
                "folder": folder or "root",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to list notes: {str(e)}")
            raise

class SearchNotesTool(BaseTool):
    """Tool for searching notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the search notes tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "search_notes"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Search for notes in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "query": {
                "type": "string",
                "description": "The search query",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "The folder to search in",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the search notes operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        query = parameters["query"]
        folder = parameters.get("folder")
        
        try:
            results = await self.note_manager.search_notes(query, folder)
            return {
                "results": results,
                "count": len(results),
                "query": query,
                "folder": folder or "root",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to search notes: {str(e)}")
            raise 
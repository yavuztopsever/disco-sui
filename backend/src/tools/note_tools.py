from typing import Dict, Any, Optional, List
from pathlib import Path
from ..core.tool_interfaces import NoteTool

class CreateNoteTool(NoteTool):
    """Tool for creating new notes."""
    name = "create_note"
    description = "Create a new note in the vault"
    
    async def forward(
        self,
        title: str,
        content: str = "",
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new note.
        
        Args:
            title: Note title
            content: Initial content
            template: Optional template name
            
        Returns:
            Dictionary containing creation results
        """
        return await self.create_note(title, content, template)

class UpdateNoteTool(NoteTool):
    """Tool for updating existing notes."""
    name = "update_note"
    description = "Update an existing note in the vault"
    
    async def forward(
        self,
        note_path: str,
        content: Optional[str] = None,
        search: Optional[str] = None,
        replace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a note's content.
        
        Args:
            note_path: Path to the note
            content: New content (if replacing entire content)
            search: Text to search for (if doing replacement)
            replace: Text to replace with
            
        Returns:
            Dictionary containing update results
        """
        return await self.update_note(
            Path(note_path),
            content,
            search,
            replace
        )

class DeleteNoteTool(NoteTool):
    """Tool for deleting notes."""
    name = "delete_note"
    description = "Delete a note from the vault"
    
    async def forward(self, note_path: str) -> Dict[str, Any]:
        """Delete a note.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Dictionary containing deletion results
        """
        return await self.delete_note(Path(note_path))

class MoveNoteTool(NoteTool):
    """Tool for moving notes."""
    name = "move_note"
    description = "Move a note to a new location"
    
    async def forward(
        self,
        source_path: str,
        target_path: str
    ) -> Dict[str, Any]:
        """Move a note.
        
        Args:
            source_path: Current note path
            target_path: New note path
            
        Returns:
            Dictionary containing move results
        """
        return await self.move_note(
            Path(source_path),
            Path(target_path)
        )

class SearchNotesTool(NoteTool):
    """Tool for searching notes."""
    name = "search_notes"
    description = "Search for notes using text or semantic search"
    
    async def forward(
        self,
        query: str,
        directory: Optional[str] = None,
        pattern: str = "*.md"
    ) -> Dict[str, Any]:
        """Search for notes.
        
        Args:
            query: Search query
            directory: Optional directory to search in
            pattern: File pattern to match
            
        Returns:
            Dictionary containing search results
        """
        results = await self.search_notes(
            query,
            Path(directory) if directory else None,
            pattern
        )
        return {
            "success": True,
            "results": results
        } 
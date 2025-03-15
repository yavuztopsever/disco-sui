"""Chat interface service for handling user interactions."""

from src.services.base_service import BaseService

class ChatInterface(BaseService):
    """Service for handling chat interactions."""
    
    async def process_question(self, question: str) -> str:
        """Process a user question."""
        return ""
        
    async def process_action(self, action: str) -> str:
        """Process a user action."""
        return ""
        
    async def format_response(self, response: dict) -> str:
        """Format a response for display."""
        return ""
        
    async def open_relevant_notes(self, notes: list[str]) -> list[str]:
        """Open relevant notes in Obsidian."""
        return [] 
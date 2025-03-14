import re
from typing import Dict, Any, Optional
from ...base_service import BaseService

class TagValidator(BaseService):
    """Service for validating Obsidian tags."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    def _initialize(self) -> None:
        """Initialize the tag validator service."""
        self.tag_pattern = re.compile(r'^[a-zA-Z0-9_/-]+$')
        self.is_running = False

    async def start(self) -> None:
        """Start the tag validator service."""
        if not self.is_running:
            self.is_running = True

    async def stop(self) -> None:
        """Stop the tag validator service."""
        if self.is_running:
            self.is_running = False

    async def health_check(self) -> bool:
        """Check if the tag validator service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        return self.is_running

    def validate_tag(self, tag: str) -> bool:
        """
        Validate a tag string.
        
        Args:
            tag (str): The tag to validate
            
        Returns:
            bool: True if the tag is valid, False otherwise
        """
        if not tag:
            return False
        
        # Remove leading '#' if present
        if tag.startswith('#'):
            tag = tag[1:]
            
        # Check if tag matches the allowed pattern
        return bool(self.tag_pattern.match(tag)) 
"""
Main email service implementation for DiscoSui.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
from pydantic import BaseModel

from ...core.config import Settings
from ...core.exceptions import EmailServiceError
from ...core.logging import get_logger
from .processor import EmailProcessor
from .importer import EmailImporter

logger = get_logger(__name__)

class EmailMetadata(BaseModel):
    """Email metadata model."""
    subject: str
    sender: str
    recipients: List[str]
    date: str
    tags: List[str]
    categories: List[str]

class EmailService:
    """Main service for handling email processing and integration."""

    def __init__(self, settings: Settings):
        """Initialize the email service."""
        self.settings = settings
        self.processor = EmailProcessor(settings)
        self.importer = EmailImporter(settings)
        self.vault_path = Path(settings.vault_path)
        self.email_path = self.vault_path / "Emails"
        self._ensure_email_directory()

    def _ensure_email_directory(self):
        """Ensure the email directory exists in the vault."""
        self.email_path.mkdir(parents=True, exist_ok=True)

    async def process_new_emails(self) -> List[Dict[str, Any]]:
        """Process new emails and integrate them into the vault."""
        try:
            # Import new emails
            new_emails = await self.importer.import_new_emails()
            
            # Process each email
            processed_emails = []
            for email in new_emails:
                try:
                    # Process email content
                    processed = await self.processor.process_email(email)
                    
                    # Create note in vault
                    note_path = await self._create_email_note(processed)
                    
                    processed_emails.append({
                        "email": processed,
                        "note_path": str(note_path)
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    continue
            
            return processed_emails

        except Exception as e:
            logger.error(f"Error in email processing: {str(e)}")
            raise EmailServiceError(f"Failed to process emails: {str(e)}")

    async def _create_email_note(self, email_data: Dict[str, Any]) -> Path:
        """Create a note for the processed email in the vault."""
        try:
            metadata = EmailMetadata(
                subject=email_data["subject"],
                sender=email_data["sender"],
                recipients=email_data["recipients"],
                date=email_data["date"],
                tags=email_data["tags"],
                categories=email_data["categories"]
            )
            
            # Generate note content using template
            note_content = self.processor.generate_note_content(email_data, metadata)
            
            # Create note file
            note_path = self.email_path / f"{email_data['date']}_{email_data['subject']}.md"
            note_path.write_text(note_content)
            
            return note_path

        except Exception as e:
            logger.error(f"Error creating email note: {str(e)}")
            raise EmailServiceError(f"Failed to create email note: {str(e)}")

    async def search_emails(self, query: str) -> List[Dict[str, Any]]:
        """Search for emails in the vault."""
        try:
            return await self.processor.search_emails(query)
        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            raise EmailServiceError(f"Failed to search emails: {str(e)}")

    async def get_email_metadata(self, note_path: str) -> EmailMetadata:
        """Get metadata for an email note."""
        try:
            return await self.processor.get_email_metadata(note_path)
        except Exception as e:
            logger.error(f"Error getting email metadata: {str(e)}")
            raise EmailServiceError(f"Failed to get email metadata: {str(e)}")

    async def update_email_categories(self, note_path: str, categories: List[str]):
        """Update categories for an email note."""
        try:
            await self.processor.update_categories(note_path, categories)
        except Exception as e:
            logger.error(f"Error updating email categories: {str(e)}")
            raise EmailServiceError(f"Failed to update email categories: {str(e)}")

    async def cleanup_old_emails(self, days: Optional[int] = None):
        """Clean up old email notes based on retention policy."""
        try:
            await self.processor.cleanup_old_emails(days)
        except Exception as e:
            logger.error(f"Error cleaning up old emails: {str(e)}")
            raise EmailServiceError(f"Failed to clean up old emails: {str(e)}") 
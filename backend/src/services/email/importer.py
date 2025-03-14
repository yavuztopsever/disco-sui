"""
Email importer for fetching and importing emails into the system.
"""

from typing import List, Dict, Any, Optional
import imaplib
import email
from email.message import Message
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

from ...core.config import Settings
from ...core.exceptions import EmailImportError
from ...core.logging import get_logger

logger = get_logger(__name__)

class EmailImporter:
    """Importer for fetching emails from IMAP servers."""

    def __init__(self, settings: Settings):
        """Initialize the email importer."""
        self.settings = settings
        self.imap_server = settings.email_imap_server
        self.imap_port = settings.email_imap_port
        self.username = settings.email_username
        self.password = settings.email_password
        self.last_import_file = Path(settings.data_path) / "last_email_import.txt"

    async def import_new_emails(self) -> List[str]:
        """Import new emails from the IMAP server."""
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.username, self.password)
            
            # Get last import date
            last_import_date = self._get_last_import_date()
            
            # Select inbox
            mail.select('inbox')
            
            # Search for new emails
            search_criteria = f'(SINCE {last_import_date.strftime("%d-%b-%Y")})'
            _, message_numbers = mail.search(None, search_criteria)
            
            # Fetch and process new emails
            new_emails = []
            for num in message_numbers[0].split():
                try:
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    new_emails.append(email_body.decode())
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            # Update last import date
            self._update_last_import_date()
            
            # Logout
            mail.logout()
            
            return new_emails

        except Exception as e:
            logger.error(f"Error importing emails: {str(e)}")
            raise EmailImportError(f"Failed to import emails: {str(e)}")

    def _get_last_import_date(self) -> datetime:
        """Get the date of the last email import."""
        try:
            if self.last_import_file.exists():
                date_str = self.last_import_file.read_text().strip()
                return datetime.fromisoformat(date_str)
            else:
                # Default to 7 days ago if no last import
                return datetime.now() - timedelta(days=7)
        except Exception as e:
            logger.error(f"Error reading last import date: {str(e)}")
            return datetime.now() - timedelta(days=7)

    def _update_last_import_date(self):
        """Update the last import date to current time."""
        try:
            self.last_import_file.write_text(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Error updating last import date: {str(e)}")

    async def import_email_attachments(self, email_data: Dict[str, Any], save_path: Path) -> List[Path]:
        """Save email attachments to the specified path."""
        try:
            saved_paths = []
            for attachment in email_data.get("attachments", []):
                try:
                    filename = attachment["filename"]
                    content = attachment["payload"]
                    
                    # Create safe filename
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                    file_path = save_path / safe_filename
                    
                    # Save attachment
                    file_path.write_bytes(content)
                    saved_paths.append(file_path)
                    
                except Exception as e:
                    logger.error(f"Error saving attachment {filename}: {str(e)}")
                    continue
            
            return saved_paths

        except Exception as e:
            logger.error(f"Error importing attachments: {str(e)}")
            raise EmailImportError(f"Failed to import attachments: {str(e)}")

    async def cleanup_imported_emails(self, days: Optional[int] = None):
        """Clean up old imported emails based on retention policy."""
        # Implementation depends on retention policy
        raise NotImplementedError("Email cleanup not implemented yet") 
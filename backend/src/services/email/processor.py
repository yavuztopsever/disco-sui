"""
Email processor implementation for parsing and processing emails.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import email
import mailparser
from datetime import datetime
import jinja2
from pydantic import BaseModel

from ...core.config import Settings
from ...core.exceptions import EmailProcessingError
from ...core.logging import get_logger

logger = get_logger(__name__)

class EmailContent(BaseModel):
    """Model for processed email content."""
    subject: str
    sender: str
    recipients: List[str]
    date: str
    body_text: str
    body_html: Optional[str]
    attachments: List[Dict[str, Any]]
    tags: List[str]
    categories: List[str]

class EmailProcessor:
    """Processor for handling email content and conversion to notes."""

    def __init__(self, settings: Settings):
        """Initialize the email processor."""
        self.settings = settings
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(settings.template_path),
            autoescape=True
        )
        self.email_template = self.template_env.get_template("email.md.j2")

    async def process_email(self, raw_email: str) -> Dict[str, Any]:
        """Process a raw email and convert it to structured content."""
        try:
            # Parse email using mailparser
            mail = mailparser.parse_from_string(raw_email)
            
            # Extract basic metadata
            content = EmailContent(
                subject=mail.subject,
                sender=mail.from_[0][1],  # Get email address
                recipients=[r[1] for r in mail.to],  # Get email addresses
                date=mail.date.strftime("%Y-%m-%d_%H-%M-%S"),
                body_text=mail.text_plain[0] if mail.text_plain else "",
                body_html=mail.text_html[0] if mail.text_html else None,
                attachments=self._process_attachments(mail.attachments),
                tags=self._generate_tags(mail),
                categories=self._categorize_email(mail)
            )
            
            return content.dict()

        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            raise EmailProcessingError(f"Failed to process email: {str(e)}")

    def _process_attachments(self, attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process email attachments."""
        processed = []
        for attachment in attachments:
            try:
                processed.append({
                    "filename": attachment["filename"],
                    "content_type": attachment["mail_content_type"],
                    "size": len(attachment["payload"]),
                    "payload": attachment["payload"]
                })
            except Exception as e:
                logger.warning(f"Error processing attachment: {str(e)}")
                continue
        return processed

    def _generate_tags(self, mail: mailparser.MailParser) -> List[str]:
        """Generate tags for the email based on content and metadata."""
        tags = ["#Email"]
        
        # Add sender domain as tag
        sender_domain = mail.from_[0][1].split("@")[1]
        tags.append(f"#Domain/{sender_domain}")
        
        # Add date-based tags
        date = mail.date
        tags.append(f"#Year/{date.year}")
        tags.append(f"#Month/{date.strftime('%B')}")
        
        return tags

    def _categorize_email(self, mail: mailparser.MailParser) -> List[str]:
        """Categorize email based on content and metadata."""
        categories = []
        
        # Add basic categories based on subject and content
        subject_lower = mail.subject.lower()
        if any(word in subject_lower for word in ["invoice", "payment", "bill"]):
            categories.append("Finance")
        elif any(word in subject_lower for word in ["meeting", "schedule", "appointment"]):
            categories.append("Meetings")
        elif any(word in subject_lower for word in ["report", "update", "status"]):
            categories.append("Reports")
        
        return categories

    def generate_note_content(self, email_data: Dict[str, Any], metadata: Any) -> str:
        """Generate note content from email data using template."""
        try:
            return self.email_template.render(
                email=email_data,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error generating note content: {str(e)}")
            raise EmailProcessingError(f"Failed to generate note content: {str(e)}")

    async def search_emails(self, query: str) -> List[Dict[str, Any]]:
        """Search for emails in the vault."""
        # Implementation depends on the search backend being used
        raise NotImplementedError("Email search not implemented yet")

    async def get_email_metadata(self, note_path: str) -> Dict[str, Any]:
        """Get metadata for an email note."""
        # Implementation depends on how metadata is stored
        raise NotImplementedError("Email metadata retrieval not implemented yet")

    async def update_categories(self, note_path: str, categories: List[str]):
        """Update categories for an email note."""
        # Implementation depends on how categories are stored
        raise NotImplementedError("Category update not implemented yet")

    async def cleanup_old_emails(self, days: Optional[int] = None):
        """Clean up old email notes based on retention policy."""
        # Implementation depends on retention policy
        raise NotImplementedError("Email cleanup not implemented yet") 
from pathlib import Path
from typing import List, Optional
from email import message_from_file
from email.message import Message
from datetime import datetime
from pydantic import BaseModel, Field
from ..base_service import BaseService
from ...core.config import Settings
from ...core.obsidian_utils import ObsidianUtils
from ...core.exceptions import EmailProcessingError

class EmailMetadata(BaseModel):
    """Metadata for processed emails."""
    sender: str = Field(..., description="Email sender address")
    subject: str = Field(..., description="Email subject")
    date: datetime = Field(..., description="Email date")
    has_attachments: bool = Field(default=False, description="Whether email has attachments")
    attachment_paths: List[str] = Field(default_factory=list, description="Paths to saved attachments")

class EmailProcessor(BaseService):
    """Service for processing email files and integrating them into the Obsidian vault."""

    def _initialize(self) -> None:
        """Initialize email processor service resources."""
        self.settings = Settings()
        self.obsidian_utils = ObsidianUtils()
        self.input_dir = Path(self.settings.RAW_EMAILS_DIR)
        self.processed_dir = Path(self.settings.PROCESSED_EMAILS_DIR)
        self.vault_path = Path(self.settings.VAULT_PATH)
        
        # Create necessary directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    async def start(self) -> None:
        """Start the email processing service."""
        try:
            await self.process_pending_emails()
        except Exception as e:
            raise EmailProcessingError(f"Failed to start email processing: {str(e)}")

    async def stop(self) -> None:
        """Stop the email processing service."""
        # Cleanup any resources if needed
        pass

    async def health_check(self) -> bool:
        """Check if the email processing service is healthy."""
        return (
            self.input_dir.exists() and
            self.processed_dir.exists() and
            self.vault_path.exists()
        )

    async def process_pending_emails(self) -> None:
        """Process all pending email files in the input directory."""
        for email_file in self.input_dir.glob("*.eml"):
            try:
                await self.process_email_file(email_file)
            except Exception as e:
                # Log error but continue processing other emails
                print(f"Error processing email {email_file}: {str(e)}")

    async def process_email_file(self, email_path: Path) -> None:
        """Process a single email file and create corresponding note.
        
        Args:
            email_path: Path to the email file
        """
        # Parse email file
        with email_path.open() as f:
            email_msg = message_from_file(f)
        
        # Extract metadata
        metadata = self._extract_metadata(email_msg)
        
        # Create note content
        note_content = self._create_note_content(email_msg, metadata)
        
        # Save attachments if any
        if email_msg.get_content_maintype() == 'multipart':
            await self._save_attachments(email_msg, metadata)
        
        # Create note in vault
        note_path = self._get_note_path(metadata)
        await self.obsidian_utils.write_note(note_path, note_content)
        
        # Move processed email to processed directory
        processed_path = self.processed_dir / email_path.name
        email_path.rename(processed_path)

    def _extract_metadata(self, email_msg: Message) -> EmailMetadata:
        """Extract metadata from email message.
        
        Args:
            email_msg: Email message object
            
        Returns:
            EmailMetadata object
        """
        return EmailMetadata(
            sender=email_msg['from'],
            subject=email_msg['subject'],
            date=datetime.strptime(email_msg['date'], '%a, %d %b %Y %H:%M:%S %z'),
            has_attachments=email_msg.get_content_maintype() == 'multipart'
        )

    def _create_note_content(self, email_msg: Message, metadata: EmailMetadata) -> str:
        """Create note content from email message.
        
        Args:
            email_msg: Email message object
            metadata: Email metadata
            
        Returns:
            Formatted note content
        """
        content = []
        
        # Add frontmatter
        content.append('---')
        content.append('type: email')
        content.append(f'sender: {metadata.sender}')
        content.append(f'date: {metadata.date.isoformat()}')
        content.append(f'subject: {metadata.subject}')
        if metadata.has_attachments:
            content.append('has_attachments: true')
            content.append('attachments:')
            for path in metadata.attachment_paths:
                content.append(f'  - {path}')
        content.append('---\n')
        
        # Add email content
        content.append(f'# {metadata.subject}\n')
        content.append(f'From: {metadata.sender}')
        content.append(f'Date: {metadata.date.strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        # Add email body
        if email_msg.get_content_maintype() == 'text':
            content.append(email_msg.get_payload())
        else:
            for part in email_msg.walk():
                if part.get_content_maintype() == 'text':
                    content.append(part.get_payload())
                    break
        
        return '\n'.join(content)

    async def _save_attachments(self, email_msg: Message, metadata: EmailMetadata) -> None:
        """Save email attachments to vault.
        
        Args:
            email_msg: Email message object
            metadata: Email metadata to update with attachment paths
        """
        attachment_dir = self.vault_path / 'attachments' / 'email'
        attachment_dir.mkdir(parents=True, exist_ok=True)
        
        for part in email_msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
                
            filename = part.get_filename()
            if filename:
                filepath = attachment_dir / filename
                with filepath.open('wb') as f:
                    f.write(part.get_payload(decode=True))
                metadata.attachment_paths.append(str(filepath.relative_to(self.vault_path)))

    def _get_note_path(self, metadata: EmailMetadata) -> Path:
        """Generate path for email note.
        
        Args:
            metadata: Email metadata
            
        Returns:
            Path object for note location
        """
        date_str = metadata.date.strftime('%Y-%m-%d')
        safe_subject = "".join(c for c in metadata.subject if c.isalnum() or c in (' ', '-', '_'))[:50]
        filename = f"{date_str} - {safe_subject}.md"
        return self.vault_path / 'emails' / filename 
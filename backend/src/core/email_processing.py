from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from email import message_from_file
from email.message import Message
from pydantic import BaseModel
from .exceptions import EmailProcessingError

class EmailMetadata(BaseModel):
    """Model for email metadata."""
    subject: str
    sender: str
    recipients: List[str]
    date: str
    has_attachments: bool
    categories: List[str] = []

class EmailProcessor:
    """Unified service for email processing operations."""
    
    def __init__(
        self,
        vault_path: Path,
        raw_emails_dir: Path,
        processed_emails_dir: Path,
        attachment_storage: Path
    ):
        self.vault_path = vault_path
        self.raw_emails_dir = raw_emails_dir
        self.processed_emails_dir = processed_emails_dir
        self.attachment_storage = attachment_storage
        
        # Create necessary directories
        self.raw_emails_dir.mkdir(parents=True, exist_ok=True)
        self.processed_emails_dir.mkdir(parents=True, exist_ok=True)
        self.attachment_storage.mkdir(parents=True, exist_ok=True)

    async def process_email(self, email_path: Path) -> Dict[str, Any]:
        """Process an email file and create a note.
        
        Args:
            email_path: Path to the email file
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Parse email
            email_msg = self._parse_email(email_path)
            
            # Extract metadata
            metadata = self._extract_metadata(email_msg)
            
            # Generate note content
            note_content = self._generate_note_content(email_msg, metadata)
            
            # Save attachments
            attachment_paths = await self._save_attachments(email_msg, email_path.stem)
            
            # Create note path
            note_path = self._generate_note_path(metadata)
            
            # Write note
            await self._write_note(note_path, note_content)
            
            # Move email to processed directory
            processed_path = self.processed_emails_dir / email_path.name
            email_path.rename(processed_path)
            
            return {
                "success": True,
                "note_path": str(note_path),
                "email_path": str(processed_path),
                "attachments": attachment_paths
            }
            
        except Exception as e:
            raise EmailProcessingError(f"Failed to process email: {str(e)}")

    async def search_emails(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        date_range: Optional[tuple[datetime, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """Search for processed emails.
        
        Args:
            query: Search query
            categories: Optional list of categories to filter by
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            List of matching email metadata
        """
        try:
            results = []
            for note_path in self.processed_emails_dir.glob("*.md"):
                content = await self._read_note(note_path)
                metadata = self._parse_note_metadata(content)
                
                # Apply filters
                if categories and not any(cat in metadata.categories for cat in categories):
                    continue
                    
                if date_range:
                    email_date = datetime.fromisoformat(metadata.date)
                    if not (date_range[0] <= email_date <= date_range[1]):
                        continue
                
                # Simple text search (could be enhanced with semantic search)
                if query.lower() in content.lower():
                    results.append({
                        "note_path": str(note_path),
                        "metadata": metadata.dict()
                    })
            
            return results
            
        except Exception as e:
            raise EmailProcessingError(f"Failed to search emails: {str(e)}")

    async def update_categories(
        self,
        note_path: Path,
        categories: List[str]
    ) -> Dict[str, Any]:
        """Update categories for an email note.
        
        Args:
            note_path: Path to the note
            categories: New categories
            
        Returns:
            Dictionary containing update results
        """
        try:
            content = await self._read_note(note_path)
            metadata = self._parse_note_metadata(content)
            
            # Update categories
            metadata.categories = categories
            
            # Update note content
            updated_content = self._update_note_metadata(content, metadata)
            await self._write_note(note_path, updated_content)
            
            return {
                "success": True,
                "note_path": str(note_path),
                "categories": categories
            }
            
        except Exception as e:
            raise EmailProcessingError(f"Failed to update categories: {str(e)}")

    async def cleanup_old_emails(
        self,
        days: int = 30,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Clean up old email files based on retention policy.
        
        Args:
            days: Number of days to retain emails
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            to_delete = []
            
            # Find old emails
            for email_path in self.processed_emails_dir.glob("*"):
                email_date = datetime.fromtimestamp(email_path.stat().st_mtime)
                if email_date < cutoff_date:
                    to_delete.append(email_path)
            
            # Delete if not dry run
            if not dry_run:
                for path in to_delete:
                    path.unlink()
            
            return {
                "success": True,
                "dry_run": dry_run,
                "deleted_count": len(to_delete),
                "deleted_paths": [str(p) for p in to_delete]
            }
            
        except Exception as e:
            raise EmailProcessingError(f"Failed to cleanup old emails: {str(e)}")

    def _parse_email(self, path: Path) -> Message:
        """Parse an email file into a Message object."""
        with open(path, 'r') as f:
            return message_from_file(f)

    def _extract_metadata(self, email_msg: Message) -> EmailMetadata:
        """Extract metadata from an email message."""
        return EmailMetadata(
            subject=email_msg.get("subject", ""),
            sender=email_msg.get("from", ""),
            recipients=email_msg.get("to", "").split(","),
            date=email_msg.get("date", ""),
            has_attachments=bool(email_msg.get_payload())
        )

    def _generate_note_content(
        self,
        email_msg: Message,
        metadata: EmailMetadata
    ) -> str:
        """Generate note content from email message."""
        content = [
            "---",
            "type: email",
            f"subject: {metadata.subject}",
            f"sender: {metadata.sender}",
            f"recipients: {', '.join(metadata.recipients)}",
            f"date: {metadata.date}",
            f"categories: {', '.join(metadata.categories)}",
            "---",
            "",
            f"# {metadata.subject}",
            "",
            "## Email Content",
            "",
            self._get_email_body(email_msg)
        ]
        return "\n".join(content)

    def _get_email_body(self, email_msg: Message) -> str:
        """Extract the email body content."""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        return email_msg.get_payload(decode=True).decode()

    async def _save_attachments(
        self,
        email_msg: Message,
        prefix: str
    ) -> List[str]:
        """Save email attachments."""
        saved_paths = []
        if email_msg.is_multipart():
            for i, part in enumerate(email_msg.walk()):
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition'):
                    filename = part.get_filename()
                    if filename:
                        path = self.attachment_storage / f"{prefix}_{filename}"
                        with open(path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        saved_paths.append(str(path))
        return saved_paths

    def _generate_note_path(self, metadata: EmailMetadata) -> Path:
        """Generate a path for the email note."""
        # Create a safe filename from the subject
        safe_subject = "".join(c if c.isalnum() else "_" for c in metadata.subject)
        return self.vault_path / "Emails" / f"{safe_subject}.md"

    async def _read_note(self, path: Path) -> str:
        """Read a note's content."""
        try:
            return path.read_text()
        except Exception as e:
            raise EmailProcessingError(f"Failed to read note {path}: {str(e)}")

    async def _write_note(self, path: Path, content: str) -> None:
        """Write content to a note."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        except Exception as e:
            raise EmailProcessingError(f"Failed to write note {path}: {str(e)}")

    def _parse_note_metadata(self, content: str) -> EmailMetadata:
        """Parse metadata from note content."""
        import yaml
        try:
            # Extract YAML frontmatter
            if content.startswith("---"):
                _, frontmatter, _ = content.split("---", 2)
                metadata = yaml.safe_load(frontmatter)
                return EmailMetadata(**metadata)
        except Exception:
            pass
        return EmailMetadata(
            subject="",
            sender="",
            recipients=[],
            date="",
            has_attachments=False
        )

    def _update_note_metadata(
        self,
        content: str,
        metadata: EmailMetadata
    ) -> str:
        """Update metadata in note content."""
        import yaml
        try:
            if content.startswith("---"):
                _, _, body = content.split("---", 2)
                frontmatter = yaml.dump(metadata.dict())
                return f"---\n{frontmatter}---\n{body}"
        except Exception:
            pass
        return content 
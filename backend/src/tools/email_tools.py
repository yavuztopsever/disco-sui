from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import email
import os
import json
from datetime import datetime
from email import policy
from email.parser import BytesParser
import mailparser

class ProcessEmailTool(BaseTool):
    name = "process_email"
    description = "Process an email file and create a note with its contents"
    inputs = {
        "email_path": {
            "type": "string",
            "description": "The path to the email file, relative to the vault root"
        },
        "note_title": {
            "type": "string",
            "description": "The title for the email note",
            "nullable": True
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the note",
            "nullable": True
        }
    }
    output_type = "object"

    def forward(self, email_path: str, note_title: Optional[str] = None, folder: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Validate paths
            if not self._validate_path(email_path):
                raise ValueError(f"Invalid email path: {email_path}")

            # Get full paths
            email_file_path = self._get_full_path(email_path)

            # Check if email file exists
            if not os.path.exists(email_file_path):
                raise FileNotFoundError(f"Email file not found: {email_path}")

            # Parse email
            with open(email_file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)

            # Generate note title if not provided
            if not note_title:
                subject = msg.get('subject', '')
                if subject:
                    # Clean subject for filename
                    subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()
                    note_title = subject[:50]  # Limit length
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    note_title = f"Email_{timestamp}"

            # Create folder if specified
            note_folder = self._get_full_path(folder) if folder else self.vault_path
            self._ensure_path_exists(note_folder)

            # Extract email content
            content = f"# {note_title}\n\n"
            content += f"## Email Details\n\n"
            content += f"- From: {msg.get('from', 'N/A')}\n"
            content += f"- To: {msg.get('to', 'N/A')}\n"
            content += f"- Date: {msg.get('date', 'N/A')}\n"
            content += f"- Subject: {msg.get('subject', 'N/A')}\n\n"

            # Process email body
            body = ""
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
                elif part.get_content_type() == "text/html":
                    # Use mailparser for better HTML handling
                    mail = mailparser.parse_from_file(email_file_path)
                    body = mail.text_plain
                    break

            if body:
                content += f"## Content\n\n{body}\n\n"

            # Process attachments
            attachments = []
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    attachments.append(filename)

            if attachments:
                content += f"## Attachments\n\n"
                for attachment in attachments:
                    content += f"- {attachment}\n"

            # Create frontmatter
            frontmatter = {
                "title": note_title,
                "type": "email",
                "email_file": email_path,
                "processing_date": datetime.now().isoformat(),
                "from": msg.get('from', ''),
                "to": msg.get('to', ''),
                "date": msg.get('date', ''),
                "subject": msg.get('subject', ''),
                "attachments": attachments
            }

            # Create note
            note_path = os.path.join(note_folder, f"{note_title}.md")
            content = self._update_frontmatter(content, frontmatter)
            self._write_file(note_path, content)

            return {
                "success": True,
                "message": f"Email file '{email_path}' processed and saved to note '{note_title}'",
                "path": os.path.relpath(note_path, self.vault_path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to process email: {str(e)}",
                "error": str(e)
            }

class ListEmailFilesTool(BaseTool):
    name = "list_email_files"
    description = "List all email files in the vault"
    inputs = {
        "folder": {
            "type": "string",
            "description": "Optional folder path to list email files from",
            "nullable": True
        },
        "extensions": {
            "type": "array",
            "description": "List of email file extensions to include",
            "default": [".eml", ".msg"],
            "items": {
                "type": "string"
            }
        }
    }
    output_type = "object"

    def forward(self, folder: Optional[str] = None, extensions: List[str] = [".eml", ".msg"]) -> Dict[str, Any]:
        try:
            # Get the target directory
            target_dir = self._get_full_path(folder) if folder else self.vault_path

            # Validate path
            if not self._validate_path(target_dir):
                raise ValueError(f"Invalid folder path: {folder}")

            # List email files
            email_files = []
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if any(file.lower().endswith(ext.lower()) for ext in extensions):
                        rel_path = os.path.relpath(os.path.join(root, file), self.vault_path)
                        email_files.append(rel_path)

            return {
                "success": True,
                "email_files": email_files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list email files: {str(e)}",
                "error": str(e)
            }

class GetEmailNoteTool(BaseTool):
    name = "get_email_note"
    description = "Get the note associated with an email file"
    inputs = {
        "email_path": {
            "type": "string",
            "description": "The path to the email file, relative to the vault root"
        }
    }
    output_type = "object"

    def forward(self, email_path: str) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(email_path):
                raise ValueError(f"Invalid email path: {email_path}")

            # Search for email notes
            email_notes = []
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        content = self._read_file(file_path)
                        frontmatter = self._get_frontmatter(content)
                        
                        # Check if this is an email note for the email file
                        if (frontmatter.get('type') == 'email' and 
                            frontmatter.get('email_file') == email_path):
                            rel_path = os.path.relpath(file_path, self.vault_path)
                            email_notes.append(rel_path)

            if not email_notes:
                return {
                    "success": False,
                    "message": f"No note found for email file '{email_path}'"
                }

            return {
                "success": True,
                "email_notes": email_notes
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get email note: {str(e)}",
                "error": str(e)
            } 
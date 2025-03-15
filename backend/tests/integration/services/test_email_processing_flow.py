"""Integration tests for email processing flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from src.core.config import Settings
from src.services.email.email_processor import EmailProcessor
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_email_file(tmp_path) -> Path:
    """Create a test email file."""
    email_path = tmp_path / "test_email.eml"
    
    # Create a test email
    msg = MIMEMultipart()
    msg['Subject'] = 'Test Email Subject'
    msg['From'] = 'sender@example.com'
    msg['To'] = 'recipient@example.com'
    msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # Add body
    body = MIMEText("This is a test email body.\n\nIt contains some content and a task: TODO: Review the project proposal.")
    msg.attach(body)
    
    # Add attachment
    attachment = MIMEApplication("Test attachment content")
    attachment.add_header('Content-Disposition', 'attachment', filename='test.txt')
    msg.attach(attachment)
    
    # Write email to file
    email_path.write_bytes(msg.as_bytes())
    
    return email_path

@pytest.fixture
def test_environment(tmp_path, test_email_file):
    """Set up test environment."""
    # Create test directories
    vault_path = tmp_path / "vault"
    email_dir = tmp_path / "emails"
    processed_dir = tmp_path / "processed_emails"
    attachments_dir = vault_path / "email_attachments"
    
    vault_path.mkdir()
    email_dir.mkdir()
    processed_dir.mkdir()
    attachments_dir.mkdir()
    
    # Copy test email to email directory
    shutil.copy(test_email_file, email_dir / "test_email.eml")
    
    return {
        "vault_path": vault_path,
        "email_dir": email_dir,
        "processed_dir": processed_dir,
        "attachments_dir": attachments_dir
    }

@pytest.mark.asyncio
async def test_email_parsing_flow(test_environment):
    """Test the email parsing flow."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        EMAIL_FILES_DIR=str(test_environment["email_dir"]),
        PROCESSED_EMAILS_DIR=str(test_environment["processed_dir"])
    )
    
    email_processor = EmailProcessor()
    await email_processor.initialize(settings)
    
    # Process email file
    email_path = test_environment["email_dir"] / "test_email.eml"
    result = await email_processor.parse_email(email_path)
    
    # Verify parsing
    assert result.success is True
    assert result.subject == "Test Email Subject"
    assert result.sender == "sender@example.com"
    assert result.body is not None
    assert "test email body" in result.body.lower()
    assert len(result.attachments) == 1
    assert result.attachments[0].filename == "test.txt"

@pytest.mark.asyncio
async def test_email_note_creation_flow(test_environment):
    """Test the creation of notes from emails."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        EMAIL_FILES_DIR=str(test_environment["email_dir"]),
        PROCESSED_EMAILS_DIR=str(test_environment["processed_dir"])
    )
    
    email_processor = EmailProcessor()
    note_manager = NoteManager()
    
    await email_processor.initialize(settings)
    await note_manager.initialize(settings)
    
    # Process email and create note
    email_path = test_environment["email_dir"] / "test_email.eml"
    email_result = await email_processor.parse_email(email_path)
    
    note_data = {
        "title": f"Email: {email_result.subject}",
        "frontmatter": {
            "email_date": email_result.date,
            "sender": email_result.sender,
            "recipients": email_result.recipients,
            "tags": ["email"]
        },
        "content": f"""# {email_result.subject}

## Email Information
- From: {email_result.sender}
- To: {', '.join(email_result.recipients)}
- Date: {email_result.date}

## Content
{email_result.body}

## Attachments
{chr(10).join([f"- [[{attachment.filename}]]" for attachment in email_result.attachments])}
"""
    }
    
    note_result = await note_manager.create_note(note_data)
    
    # Verify note creation
    assert note_result.success is True
    note_path = test_environment["vault_path"] / f"Email - {email_result.subject}.md"
    assert note_path.exists()
    
    # Verify note content
    content = note_path.read_text()
    assert email_result.subject in content
    assert email_result.sender in content
    assert email_result.body in content
    assert "test.txt" in content

@pytest.mark.asyncio
async def test_email_attachment_handling_flow(test_environment):
    """Test the handling of email attachments."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        EMAIL_FILES_DIR=str(test_environment["email_dir"]),
        PROCESSED_EMAILS_DIR=str(test_environment["processed_dir"]),
        EMAIL_ATTACHMENTS_DIR=str(test_environment["attachments_dir"])
    )
    
    email_processor = EmailProcessor()
    await email_processor.initialize(settings)
    
    # Process email attachments
    email_path = test_environment["email_dir"] / "test_email.eml"
    result = await email_processor.process_attachments(email_path)
    
    # Verify attachment processing
    assert result.success is True
    assert len(result.saved_attachments) == 1
    
    # Verify attachment files
    attachment_path = test_environment["attachments_dir"] / "test.txt"
    assert attachment_path.exists()
    assert "Test attachment content" in attachment_path.read_text()

@pytest.mark.asyncio
async def test_email_task_extraction_flow(test_environment):
    """Test the extraction of tasks from emails."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        EMAIL_FILES_DIR=str(test_environment["email_dir"])
    )
    
    email_processor = EmailProcessor()
    await email_processor.initialize(settings)
    
    # Process email and extract tasks
    email_path = test_environment["email_dir"] / "test_email.eml"
    email_result = await email_processor.parse_email(email_path)
    task_result = await email_processor.extract_tasks(email_result.body)
    
    # Verify task extraction
    assert task_result.success is True
    assert task_result.tasks is not None
    assert len(task_result.tasks) > 0
    assert any("Review the project proposal" in task for task in task_result.tasks)
    
    # Create task note
    task_note_path = test_environment["vault_path"] / "Email Tasks.md"
    task_content = "# Tasks from Email\n\n"
    for task in task_result.tasks:
        task_content += f"- [ ] {task}\n"
    
    task_note_path.write_text(task_content)
    
    # Verify task note
    assert task_note_path.exists()
    content = task_note_path.read_text()
    assert "Tasks from Email" in content
    assert all(task in content for task in task_result.tasks) 
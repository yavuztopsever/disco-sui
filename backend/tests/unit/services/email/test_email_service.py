import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.email.email_service import EmailService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_importer():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def email_service(mock_context, mock_processor, mock_importer, mock_storage):
    return EmailService(
        context=mock_context,
        processor=mock_processor,
        importer=mock_importer,
        storage=mock_storage
    )

def test_service_initialization(email_service):
    """Test email service initialization."""
    assert email_service is not None
    assert email_service.context is not None
    assert email_service._processor is not None
    assert email_service._importer is not None

def test_process_email(email_service, mock_processor):
    """Test processing an email."""
    email_data = {
        "subject": "Test Email",
        "body": "Test content",
        "attachments": []
    }
    mock_processor.process_email.return_value = {
        "success": True,
        "processed": True,
        "note_path": "emails/test_email.md"
    }
    
    result = email_service.process_email(email_data)
    assert result["success"] is True
    assert result["processed"] is True
    assert "note_path" in result
    mock_processor.process_email.assert_called_once_with(email_data)

def test_import_emails(email_service, mock_importer):
    """Test importing emails."""
    mock_importer.import_emails.return_value = {
        "success": True,
        "imported": 5,
        "failed": 0
    }
    
    result = email_service.import_emails()
    assert result["success"] is True
    assert result["imported"] == 5
    assert result["failed"] == 0
    mock_importer.import_emails.assert_called_once()

def test_process_attachments(email_service, mock_processor):
    """Test processing email attachments."""
    attachments = [
        {"name": "doc1.pdf", "content": b"content1"},
        {"name": "doc2.docx", "content": b"content2"}
    ]
    mock_processor.process_attachments.return_value = {
        "success": True,
        "processed": 2,
        "paths": ["attachments/doc1.pdf", "attachments/doc2.docx"]
    }
    
    result = email_service.process_attachments(attachments)
    assert result["success"] is True
    assert result["processed"] == 2
    assert len(result["paths"]) == 2
    mock_processor.process_attachments.assert_called_once_with(attachments)

def test_get_email_metadata(email_service, mock_processor):
    """Test getting email metadata."""
    email_data = {
        "subject": "Test Email",
        "from": "sender@example.com",
        "date": "2024-03-14"
    }
    mock_processor.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "subject": "Test Email",
            "sender": "sender@example.com",
            "date": "2024-03-14",
            "tags": ["email"]
        }
    }
    
    result = email_service.get_email_metadata(email_data)
    assert result["success"] is True
    assert "metadata" in result
    assert "subject" in result["metadata"]
    mock_processor.extract_metadata.assert_called_once_with(email_data)

def test_configure_email_source(email_service, mock_importer):
    """Test configuring email source."""
    config = {
        "host": "imap.example.com",
        "username": "user@example.com",
        "password": "password123"
    }
    mock_importer.configure_source.return_value = {
        "success": True,
        "configured": True
    }
    
    result = email_service.configure_email_source(config)
    assert result["success"] is True
    assert result["configured"] is True
    mock_importer.configure_source.assert_called_once_with(config)

def test_get_import_status(email_service, mock_importer):
    """Test getting import status."""
    mock_importer.get_status.return_value = {
        "success": True,
        "status": "idle",
        "last_import": "2024-03-14 12:00:00",
        "pending": 0
    }
    
    result = email_service.get_import_status()
    assert result["success"] is True
    assert "status" in result
    assert "last_import" in result
    mock_importer.get_status.assert_called_once()

def test_error_handling_process(email_service, mock_processor):
    """Test error handling during email processing."""
    mock_processor.process_email.side_effect = Exception("Processing error")
    
    result = email_service.process_email({})
    assert result["success"] is False
    assert "error" in result

def test_error_handling_import(email_service, mock_importer):
    """Test error handling during email import."""
    mock_importer.import_emails.side_effect = Exception("Import error")
    
    result = email_service.import_emails()
    assert result["success"] is False
    assert "error" in result

def test_batch_process_emails(email_service, mock_processor):
    """Test batch processing emails."""
    emails = [
        {"subject": "Email 1", "body": "Content 1"},
        {"subject": "Email 2", "body": "Content 2"}
    ]
    mock_processor.batch_process.return_value = {
        "success": True,
        "processed": 2,
        "failed": 0,
        "notes": ["note1.md", "note2.md"]
    }
    
    result = email_service.batch_process_emails(emails)
    assert result["success"] is True
    assert result["processed"] == 2
    assert result["failed"] == 0
    assert len(result["notes"]) == 2
    mock_processor.batch_process.assert_called_once_with(emails)

def test_validate_email_format(email_service, mock_processor):
    """Test validating email format."""
    email_data = {
        "subject": "Test Email",
        "body": "Content"
    }
    mock_processor.validate_format.return_value = {
        "success": True,
        "valid": True,
        "format": "text/plain"
    }
    
    result = email_service.validate_email_format(email_data)
    assert result["success"] is True
    assert result["valid"] is True
    assert "format" in result
    mock_processor.validate_format.assert_called_once_with(email_data)

def test_get_email_statistics(email_service, mock_processor):
    """Test getting email statistics."""
    mock_processor.get_statistics.return_value = {
        "success": True,
        "total_processed": 100,
        "total_failed": 5,
        "average_size": 1024
    }
    
    result = email_service.get_statistics()
    assert result["success"] is True
    assert "total_processed" in result
    assert "total_failed" in result
    mock_processor.get_statistics.assert_called_once()

def test_cleanup_processed_emails(email_service, mock_processor):
    """Test cleaning up processed emails."""
    mock_processor.cleanup.return_value = {
        "success": True,
        "cleaned": 10,
        "remaining": 0
    }
    
    result = email_service.cleanup_processed()
    assert result["success"] is True
    assert "cleaned" in result
    assert "remaining" in result
    mock_processor.cleanup.assert_called_once()

def test_get_email_templates(email_service, mock_processor):
    """Test getting email templates."""
    mock_processor.get_templates.return_value = {
        "success": True,
        "templates": ["template1", "template2"],
        "count": 2
    }
    
    result = email_service.get_templates()
    assert result["success"] is True
    assert "templates" in result
    assert "count" in result
    mock_processor.get_templates.assert_called_once()

def test_update_email_template(email_service, mock_processor):
    """Test updating email template."""
    template_data = {
        "name": "template1",
        "content": "Template content"
    }
    mock_processor.update_template.return_value = {
        "success": True,
        "updated": True,
        "template": "template1"
    }
    
    result = email_service.update_template(template_data)
    assert result["success"] is True
    assert result["updated"] is True
    assert "template" in result
    mock_processor.update_template.assert_called_once_with(template_data)

def test_get_service_config(email_service):
    """Test getting service configuration."""
    result = email_service.get_config()
    assert result["success"] is True
    assert "config" in result
    assert isinstance(result["config"], dict)

def test_update_service_config(email_service):
    """Test updating service configuration."""
    config_update = {
        "auto_import": True,
        "import_interval": 3600,
        "cleanup_after": 7
    }
    
    result = email_service.update_config(config_update)
    assert result["success"] is True
    assert result["config"] == config_update 
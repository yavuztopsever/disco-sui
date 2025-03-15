import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.email.importer import EmailImporter

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def mock_imap():
    return MagicMock()

@pytest.fixture
def email_importer(mock_context, mock_processor, mock_imap):
    importer = EmailImporter(context=mock_context)
    importer._processor = mock_processor
    importer._imap = mock_imap
    return importer

def test_importer_initialization(email_importer):
    """Test email importer initialization."""
    assert email_importer is not None
    assert email_importer.context is not None
    assert email_importer._processor is not None
    assert email_importer._imap is not None

def test_configure_source(email_importer, mock_imap):
    """Test configuring email source."""
    config = {
        "host": "imap.example.com",
        "username": "user@example.com",
        "password": "password123",
        "port": 993,
        "ssl": True
    }
    mock_imap.login.return_value = True
    
    result = email_importer.configure_source(config)
    assert result["success"] is True
    assert result["configured"] is True
    mock_imap.login.assert_called_once_with(config["username"], config["password"])

def test_import_emails(email_importer, mock_imap, mock_processor):
    """Test importing emails."""
    mock_imap.search.return_value = (True, [b"1 2 3"])
    mock_imap.fetch.return_value = (True, {
        b"1": {"RFC822": b"email1"},
        b"2": {"RFC822": b"email2"},
        b"3": {"RFC822": b"email3"}
    })
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_emails()
    assert result["success"] is True
    assert result["imported"] == 3
    assert result["failed"] == 0
    assert mock_processor.process_email.call_count == 3

def test_import_from_folder(email_importer, mock_imap, mock_processor):
    """Test importing emails from specific folder."""
    folder = "INBOX/Archive"
    mock_imap.select_folder.return_value = True
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_from_folder(folder)
    assert result["success"] is True
    assert result["imported"] == 1
    assert result["folder"] == folder
    mock_imap.select_folder.assert_called_once_with(folder)

def test_list_folders(email_importer, mock_imap):
    """Test listing email folders."""
    mock_imap.list.return_value = (True, [
        b'(\\HasNoChildren) "/" "INBOX"',
        b'(\\HasChildren) "/" "Archive"'
    ])
    
    result = email_importer.list_folders()
    assert result["success"] is True
    assert "folders" in result
    assert len(result["folders"]) == 2
    mock_imap.list.assert_called_once()

def test_import_by_date(email_importer, mock_imap, mock_processor):
    """Test importing emails by date range."""
    start_date = "2024-03-01"
    end_date = "2024-03-14"
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_by_date(start_date, end_date)
    assert result["success"] is True
    assert result["imported"] == 1
    assert "date_range" in result
    mock_imap.search.assert_called_once()

def test_import_by_sender(email_importer, mock_imap, mock_processor):
    """Test importing emails by sender."""
    sender = "sender@example.com"
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_by_sender(sender)
    assert result["success"] is True
    assert result["imported"] == 1
    assert result["sender"] == sender
    mock_imap.search.assert_called_once()

def test_error_handling_connection(email_importer, mock_imap):
    """Test error handling for connection issues."""
    mock_imap.login.side_effect = Exception("Connection error")
    
    result = email_importer.configure_source({
        "host": "imap.example.com",
        "username": "user",
        "password": "pass"
    })
    assert result["success"] is False
    assert "error" in result

def test_error_handling_import(email_importer, mock_imap, mock_processor):
    """Test error handling during import."""
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.side_effect = Exception("Processing error")
    
    result = email_importer.import_emails()
    assert result["success"] is True  # Overall import succeeds
    assert result["imported"] == 0
    assert result["failed"] == 1

def test_get_status(email_importer):
    """Test getting importer status."""
    result = email_importer.get_status()
    assert result["success"] is True
    assert "status" in result
    assert "last_import" in result
    assert "pending" in result

def test_validate_config(email_importer):
    """Test validating email source configuration."""
    valid_config = {
        "host": "imap.example.com",
        "username": "user@example.com",
        "password": "password123",
        "port": 993,
        "ssl": True
    }
    
    result = email_importer.validate_config(valid_config)
    assert result["success"] is True
    assert result["valid"] is True
    assert "config" in result

def test_import_with_filters(email_importer, mock_imap, mock_processor):
    """Test importing emails with filters."""
    filters = {
        "subject": "Test",
        "has_attachments": True,
        "min_size": 1000
    }
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_with_filters(filters)
    assert result["success"] is True
    assert result["imported"] == 1
    assert "filters" in result
    mock_imap.search.assert_called_once()

def test_batch_import(email_importer, mock_imap, mock_processor):
    """Test batch importing emails."""
    email_ids = [b"1", b"2"]
    mock_imap.fetch.return_value = (True, {
        b"1": {"RFC822": b"email1"},
        b"2": {"RFC822": b"email2"}
    })
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.batch_import(email_ids)
    assert result["success"] is True
    assert result["imported"] == 2
    assert result["failed"] == 0
    assert mock_processor.process_email.call_count == 2

def test_import_attachments_only(email_importer, mock_imap, mock_processor):
    """Test importing only emails with attachments."""
    mock_imap.search.return_value = (True, [b"1"])
    mock_imap.fetch.return_value = (True, {b"1": {"RFC822": b"email1"}})
    mock_processor.process_email.return_value = {"success": True}
    
    result = email_importer.import_attachments_only()
    assert result["success"] is True
    assert "imported" in result
    assert "attachments" in result
    mock_imap.search.assert_called_once()

def test_cleanup_imported(email_importer, mock_imap):
    """Test cleaning up imported emails."""
    mock_imap.store.return_value = (True, None)
    
    result = email_importer.cleanup_imported([b"1", b"2"])
    assert result["success"] is True
    assert "cleaned" in result
    mock_imap.store.assert_called_once()

def test_get_import_statistics(email_importer):
    """Test getting import statistics."""
    result = email_importer.get_statistics()
    assert result["success"] is True
    assert "total_imported" in result
    assert "total_failed" in result
    assert "last_import_time" in result

def test_validate_connection(email_importer, mock_imap):
    """Test validating email connection."""
    mock_imap.noop.return_value = (True, None)
    
    result = email_importer.validate_connection()
    assert result["success"] is True
    assert result["connected"] is True
    mock_imap.noop.assert_called_once()

def test_get_folder_statistics(email_importer, mock_imap):
    """Test getting folder statistics."""
    folder = "INBOX"
    mock_imap.select_folder.return_value = True
    mock_imap.status.return_value = (True, {
        b"MESSAGES": b"100",
        b"UNSEEN": b"10"
    })
    
    result = email_importer.get_folder_statistics(folder)
    assert result["success"] is True
    assert "total" in result
    assert "unread" in result
    mock_imap.select_folder.assert_called_once_with(folder) 
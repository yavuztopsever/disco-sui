import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from email.message import EmailMessage
from src.services.email.email_processor import EmailProcessor

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def mock_email_message():
    email = EmailMessage()
    email["Subject"] = "Test Email"
    email["From"] = "sender@example.com"
    email["To"] = "recipient@example.com"
    email["Date"] = "Thu, 1 Jan 2024 12:00:00 +0000"
    email.set_content("Test email content")
    return email

@pytest.fixture
def email_processor(mock_context, mock_storage):
    return EmailProcessor(
        context=mock_context,
        storage=mock_storage
    )

def test_email_processor_initialization(email_processor):
    """Test email processor initialization."""
    assert email_processor is not None
    assert email_processor.storage is not None

def test_process_email_file(email_processor, mock_email_message):
    """Test processing email file."""
    email_path = "test/email.eml"
    with patch("builtins.open", mock_open(read_data=str(mock_email_message))):
        result = email_processor.process_email_file(email_path)
        assert result["success"] is True
        assert result["email_data"]["subject"] == "Test Email"
        assert result["email_data"]["from"] == "sender@example.com"

def test_extract_email_metadata(email_processor, mock_email_message):
    """Test extracting email metadata."""
    result = email_processor.extract_metadata(mock_email_message)
    assert result["success"] is True
    assert result["metadata"]["subject"] == "Test Email"
    assert result["metadata"]["from"] == "sender@example.com"
    assert "date" in result["metadata"]

def test_process_email_content(email_processor, mock_email_message):
    """Test processing email content."""
    result = email_processor.process_content(mock_email_message)
    assert result["success"] is True
    assert "content" in result
    assert "html_content" in result
    assert "plain_content" in result

def test_process_attachments(email_processor, mock_email_message):
    """Test processing email attachments."""
    # Add attachment to mock email
    attachment_data = b"Test attachment content"
    mock_email_message.add_attachment(
        attachment_data,
        maintype="application",
        subtype="pdf",
        filename="test.pdf"
    )
    
    with patch("pathlib.Path.write_bytes") as mock_write:
        result = email_processor.process_attachments(mock_email_message)
        assert result["success"] is True
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["filename"] == "test.pdf"
        mock_write.assert_called_once_with(attachment_data)

def test_create_note_content(email_processor, mock_email_message):
    """Test creating note content from email."""
    result = email_processor.create_note_content(mock_email_message)
    assert result["success"] is True
    assert "# Test Email" in result["content"]
    assert "sender@example.com" in result["content"]
    assert "Test email content" in result["content"]

def test_analyze_thread(email_processor):
    """Test analyzing email thread."""
    thread_emails = [
        {
            "subject": "Re: Test Thread",
            "from": "user1@example.com",
            "date": "2024-01-01T12:00:00",
            "content": "Reply 1"
        },
        {
            "subject": "Test Thread",
            "from": "user2@example.com",
            "date": "2024-01-01T11:00:00",
            "content": "Original message"
        }
    ]
    
    result = email_processor.analyze_thread(thread_emails)
    assert result["success"] is True
    assert result["thread_analysis"]["message_count"] == 2
    assert len(result["thread_analysis"]["participants"]) == 2

def test_extract_recipients(email_processor, mock_email_message):
    """Test extracting email recipients."""
    result = email_processor.extract_recipients(mock_email_message)
    assert result["success"] is True
    assert "recipient@example.com" in result["recipients"]

def test_parse_email_date(email_processor, mock_email_message):
    """Test parsing email date."""
    result = email_processor.parse_date(mock_email_message["Date"])
    assert result["success"] is True
    assert "parsed_date" in result
    assert result["parsed_date"].year == 2024

def test_error_handling(email_processor):
    """Test error handling for invalid email."""
    invalid_email_path = "non_existent.eml"
    result = email_processor.process_email_file(invalid_email_path)
    assert result["success"] is False
    assert "error" in result

def test_handle_multipart_email(email_processor):
    """Test handling multipart email."""
    multipart_email = EmailMessage()
    multipart_email["Subject"] = "Multipart Test"
    multipart_email.make_mixed()
    multipart_email.add_alternative("Plain text content")
    multipart_email.add_alternative("<p>HTML content</p>", subtype="html")
    
    result = email_processor.process_content(multipart_email)
    assert result["success"] is True
    assert "plain_content" in result
    assert "html_content" in result

def test_sanitize_email_content(email_processor):
    """Test sanitizing email content."""
    unsafe_content = "<script>alert('xss')</script><p>Safe content</p>"
    result = email_processor.sanitize_content(unsafe_content)
    assert result["success"] is True
    assert "<script>" not in result["content"]
    assert "Safe content" in result["content"] 
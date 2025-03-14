"""Pytest configuration and fixtures."""

import os
import pytest
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import MagicMock

@pytest.fixture
def test_vault_path(tmp_path) -> Path:
    """Create a temporary vault path."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    return vault_path

@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings."""
    settings = MagicMock()
    settings.VAULT_PATH = "/test/vault"
    settings.AUDIO_FILES_DIR = "/test/audio"
    settings.RAW_EMAILS_DIR = "/test/emails/raw"
    settings.PROCESSED_EMAILS_DIR = "/test/emails/processed"
    settings.RAG_VECTOR_DB_PATH = "/test/vector_db"
    settings.RAG_CHUNK_SIZE = 512
    settings.RAG_CHUNK_OVERLAP = 128
    return settings

@pytest.fixture
def mock_obsidian_utils() -> MagicMock:
    """Create mock ObsidianUtils."""
    return MagicMock()

@pytest.fixture
def mock_llm() -> MagicMock:
    """Create mock LLM."""
    return MagicMock()

@pytest.fixture
def mock_vector_db() -> MagicMock:
    """Create mock vector database."""
    return MagicMock()

@pytest.fixture
def mock_semantic_analyzer() -> Generator[MagicMock, None, None]:
    mock = MagicMock()
    mock.analyze_note.return_value = {
        "success": True,
        "analysis": {
            "topics": ["test"],
            "entities": ["test"],
            "summary": "test"
        }
    }
    mock.find_related_notes.return_value = {
        "success": True,
        "related_notes": ["test/note1.md", "test/note2.md"]
    }
    mock.generate_knowledge_graph.return_value = {
        "success": True,
        "graph": {
            "nodes": [],
            "edges": []
        }
    }
    yield mock

@pytest.fixture
def mock_text_processor() -> Generator[MagicMock, None, None]:
    mock = MagicMock()
    mock.chunk_text.return_value = {
        "success": True,
        "chunks": ["chunk1", "chunk2"]
    }
    mock.extract_entities.return_value = {
        "success": True,
        "entities": [
            {"text": "John Smith", "type": "PERSON"},
            {"text": "Microsoft", "type": "ORG"}
        ]
    }
    mock.summarize_text.return_value = {
        "success": True,
        "summary": "Test summary"
    }
    mock.analyze_sentiment.return_value = {
        "success": True,
        "sentiment": {
            "polarity": 0.5,
            "subjectivity": 0.5
        }
    }
    yield mock

@pytest.fixture
def mock_email_processor() -> Generator[MagicMock, None, None]:
    mock = MagicMock()
    mock.process_email.return_value = {
        "success": True,
        "processed_data": {
            "subject": "Test Email",
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "date": "2024-01-01T12:00:00+00:00",
            "content": "Test content"
        }
    }
    mock.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "subject": "Test Email",
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "date": "2024-01-01T12:00:00+00:00"
        }
    }
    mock.convert_to_note.return_value = {
        "success": True,
        "note_data": {
            "title": "Test Email",
            "content": "Test content",
            "path": "test/test_email.md"
        }
    }
    mock.analyze_thread.return_value = {
        "success": True,
        "thread_analysis": {
            "messages": 1,
            "participants": ["sender@example.com", "recipient@example.com"],
            "timeline": ["2024-01-01T12:00:00+00:00"]
        }
    }
    mock.list_email_files.return_value = {
        "success": True,
        "email_files": ["test/email1.eml", "test/email2.eml"]
    }
    mock.get_email_note.return_value = {
        "success": True,
        "note_data": {
            "title": "Test Email",
            "content": "Test content",
            "path": "test/test_email.md"
        }
    }
    mock.import_emails.return_value = {
        "success": True,
        "imported_emails": ["test/email1.eml", "test/email2.eml"]
    }
    mock.export_emails.return_value = {
        "success": True,
        "exported_files": ["test/output.pdf"]
    }
    yield mock

@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    
    # Create sample note
    note_dir = data_dir / "test"
    note_dir.mkdir()
    sample_note = note_dir / "sample_note.md"
    sample_note.write_text("""# Sample Note
    
This is a sample note for testing purposes.
It contains some test content that can be analyzed.
""")
    
    # Create sample email
    email_dir = note_dir
    sample_email = email_dir / "sample_email.eml"
    sample_email.write_text("""From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Thu, 1 Jan 2024 12:00:00 +0000

This is a test email message.
It contains multiple lines of text
and some attachments.

Best regards,
Sender""")
    
    return data_dir

@pytest.fixture
def test_vault_path(test_data_dir: Path) -> str:
    """Return the path to the test vault."""
    return str(test_data_dir) 
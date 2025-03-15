import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.manipulation.note_manager import NoteManager

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def mock_processor():
    return MagicMock()

@pytest.fixture
def note_manager(mock_context, mock_storage, mock_processor):
    return NoteManager(
        context=mock_context,
        storage=mock_storage,
        processor=mock_processor
    )

def test_note_manager_initialization(note_manager):
    """Test note manager initialization."""
    assert note_manager is not None
    assert note_manager.storage is not None
    assert note_manager.processor is not None

def test_create_note(note_manager, mock_storage):
    """Test note creation."""
    title = "Test Note"
    content = "# Test Content"
    mock_storage.create_note.return_value = {
        "success": True,
        "path": "notes/test_note.md"
    }
    
    result = note_manager.create_note(title, content)
    assert result["success"] is True
    assert "path" in result
    mock_storage.create_note.assert_called_once()

def test_update_note(note_manager, mock_storage):
    """Test note updating."""
    note_path = "notes/test_note.md"
    new_content = "# Updated Content"
    mock_storage.update_note.return_value = {
        "success": True,
        "path": note_path
    }
    
    result = note_manager.update_note(note_path, new_content)
    assert result["success"] is True
    assert result["path"] == note_path

def test_delete_note(note_manager, mock_storage):
    """Test note deletion."""
    note_path = "notes/test_note.md"
    mock_storage.delete_note.return_value = {
        "success": True,
        "deleted": True
    }
    
    result = note_manager.delete_note(note_path)
    assert result["success"] is True
    assert result["deleted"] is True

def test_move_note(note_manager, mock_storage):
    """Test note movement."""
    source = "old/path/note.md"
    target = "new/path/note.md"
    mock_storage.move_note.return_value = {
        "success": True,
        "new_path": target
    }
    
    result = note_manager.move_note(source, target)
    assert result["success"] is True
    assert result["new_path"] == target

def test_copy_note(note_manager, mock_storage):
    """Test note copying."""
    source = "source/note.md"
    target = "target/note.md"
    mock_storage.copy_note.return_value = {
        "success": True,
        "new_path": target
    }
    
    result = note_manager.copy_note(source, target)
    assert result["success"] is True
    assert result["new_path"] == target

def test_get_note_content(note_manager, mock_storage):
    """Test getting note content."""
    note_path = "notes/test_note.md"
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "# Test Content"
    }
    
    result = note_manager.get_note_content(note_path)
    assert result["success"] is True
    assert "content" in result

def test_get_note_metadata(note_manager, mock_processor):
    """Test getting note metadata."""
    note_path = "notes/test_note.md"
    content = """---
title: Test Note
tags: [test]
---
# Content"""
    mock_processor.extract_metadata.return_value = {
        "success": True,
        "metadata": {
            "title": "Test Note",
            "tags": ["test"]
        }
    }
    
    result = note_manager.get_note_metadata(note_path, content)
    assert result["success"] is True
    assert "metadata" in result
    assert result["metadata"]["title"] == "Test Note"

def test_update_note_metadata(note_manager, mock_processor, mock_storage):
    """Test updating note metadata."""
    note_path = "notes/test_note.md"
    updates = {
        "title": "Updated Title",
        "tags": ["new", "tags"]
    }
    mock_processor.update_metadata.return_value = {
        "success": True,
        "content": "Updated content"
    }
    mock_storage.update_note.return_value = {
        "success": True,
        "path": note_path
    }
    
    result = note_manager.update_note_metadata(note_path, updates)
    assert result["success"] is True
    assert "path" in result

def test_list_notes(note_manager, mock_storage):
    """Test listing notes."""
    mock_storage.list_notes.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md"]
    }
    
    result = note_manager.list_notes()
    assert result["success"] is True
    assert len(result["notes"]) == 2

def test_search_notes(note_manager, mock_storage):
    """Test searching notes."""
    query = "test"
    mock_storage.search_notes.return_value = {
        "success": True,
        "results": [
            {"path": "note1.md", "score": 0.9},
            {"path": "note2.md", "score": 0.8}
        ]
    }
    
    result = note_manager.search_notes(query)
    assert result["success"] is True
    assert len(result["results"]) == 2

def test_validate_note(note_manager, mock_processor):
    """Test note validation."""
    content = "# Valid Note"
    mock_processor.validate_content.return_value = {
        "success": True,
        "valid": True,
        "issues": []
    }
    
    result = note_manager.validate_note(content)
    assert result["success"] is True
    assert result["valid"] is True

def test_error_handling(note_manager, mock_storage):
    """Test error handling."""
    mock_storage.create_note.side_effect = Exception("Test error")
    
    result = note_manager.create_note("Test", "Content")
    assert result["success"] is False
    assert "error" in result

def test_batch_operation(note_manager):
    """Test batch note operation."""
    operations = [
        {"type": "create", "title": "Note 1", "content": "Content 1"},
        {"type": "create", "title": "Note 2", "content": "Content 2"}
    ]
    
    result = note_manager.batch_operation(operations)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == len(operations)

def test_get_note_links(note_manager, mock_processor):
    """Test getting note links."""
    content = """# Test
[[link1.md|Link 1]]
[[link2.md|Link 2]]"""
    mock_processor.process_links.return_value = {
        "success": True,
        "links": [
            {"text": "Link 1", "target": "link1.md"},
            {"text": "Link 2", "target": "link2.md"}
        ]
    }
    
    result = note_manager.get_note_links(content)
    assert result["success"] is True
    assert len(result["links"]) == 2 
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.organization.tags.tag_manager import TagManager

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_validator():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def tag_manager(mock_context, mock_validator, mock_storage):
    return TagManager(
        context=mock_context,
        validator=mock_validator,
        storage=mock_storage
    )

def test_tag_manager_initialization(tag_manager):
    """Test tag manager initialization."""
    assert tag_manager is not None
    assert tag_manager.validator is not None
    assert tag_manager.storage is not None

def test_add_tag(tag_manager, mock_validator, mock_storage):
    """Test adding a tag."""
    tag = "project"
    mock_validator.validate_tag.return_value = {"success": True, "valid": True}
    mock_storage.add_tag.return_value = {"success": True, "tag": tag}
    
    result = tag_manager.add_tag(tag)
    assert result["success"] is True
    assert result["tag"] == tag
    mock_validator.validate_tag.assert_called_with(tag)

def test_remove_tag(tag_manager, mock_storage):
    """Test removing a tag."""
    tag = "project"
    mock_storage.remove_tag.return_value = {"success": True, "removed": True}
    
    result = tag_manager.remove_tag(tag)
    assert result["success"] is True
    assert result["removed"] is True

def test_list_tags(tag_manager, mock_storage):
    """Test listing tags."""
    mock_storage.get_tags.return_value = {
        "success": True,
        "tags": ["project", "todo", "urgent"]
    }
    
    result = tag_manager.list_tags()
    assert result["success"] is True
    assert isinstance(result["tags"], list)
    assert len(result["tags"]) == 3

def test_update_tag(tag_manager, mock_validator, mock_storage):
    """Test updating a tag."""
    old_tag = "project"
    new_tag = "active-project"
    mock_validator.validate_tag.return_value = {"success": True, "valid": True}
    mock_storage.update_tag.return_value = {
        "success": True,
        "old_tag": old_tag,
        "new_tag": new_tag
    }
    
    result = tag_manager.update_tag(old_tag, new_tag)
    assert result["success"] is True
    assert result["old_tag"] == old_tag
    assert result["new_tag"] == new_tag

def test_get_tag_usage(tag_manager, mock_storage):
    """Test getting tag usage statistics."""
    tag = "project"
    mock_storage.get_tag_usage.return_value = {
        "success": True,
        "usage": {
            "count": 5,
            "notes": ["note1.md", "note2.md"],
            "last_used": "2024-01-01"
        }
    }
    
    result = tag_manager.get_tag_usage(tag)
    assert result["success"] is True
    assert "usage" in result
    assert result["usage"]["count"] == 5

def test_validate_tag_format(tag_manager, mock_validator):
    """Test tag format validation."""
    tag = "invalid tag!"
    mock_validator.validate_tag.return_value = {
        "success": True,
        "valid": False,
        "errors": ["Invalid characters in tag"]
    }
    
    result = tag_manager.add_tag(tag)
    assert result["success"] is False
    assert "errors" in result

def test_batch_add_tags(tag_manager, mock_validator, mock_storage):
    """Test batch adding tags."""
    tags = ["project", "todo", "urgent"]
    mock_validator.validate_tag.return_value = {"success": True, "valid": True}
    mock_storage.batch_add_tags.return_value = {
        "success": True,
        "added": len(tags),
        "failed": 0
    }
    
    result = tag_manager.batch_add_tags(tags)
    assert result["success"] is True
    assert result["added"] == len(tags)
    assert result["failed"] == 0

def test_get_tag_categories(tag_manager, mock_storage):
    """Test getting tag categories."""
    mock_storage.get_tag_categories.return_value = {
        "success": True,
        "categories": {
            "status": ["todo", "done"],
            "priority": ["urgent", "normal"],
            "type": ["project", "note"]
        }
    }
    
    result = tag_manager.get_tag_categories()
    assert result["success"] is True
    assert "categories" in result
    assert len(result["categories"]) == 3

def test_error_handling_duplicate_tag(tag_manager, mock_validator, mock_storage):
    """Test error handling for duplicate tag."""
    tag = "project"
    mock_validator.validate_tag.return_value = {"success": True, "valid": True}
    mock_storage.add_tag.side_effect = Exception("Tag already exists")
    
    result = tag_manager.add_tag(tag)
    assert result["success"] is False
    assert "error" in result

def test_search_tags(tag_manager, mock_storage):
    """Test searching tags."""
    query = "proj"
    mock_storage.search_tags.return_value = {
        "success": True,
        "results": [
            {"tag": "project", "score": 1.0},
            {"tag": "project-archive", "score": 0.8}
        ]
    }
    
    result = tag_manager.search_tags(query)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == 2

def test_get_related_tags(tag_manager, mock_storage):
    """Test getting related tags."""
    tag = "project"
    mock_storage.get_related_tags.return_value = {
        "success": True,
        "related": [
            {"tag": "todo", "strength": 0.8},
            {"tag": "active", "strength": 0.6}
        ]
    }
    
    result = tag_manager.get_related_tags(tag)
    assert result["success"] is True
    assert "related" in result
    assert len(result["related"]) == 2

def test_validate_tags(tag_manager, mock_validator):
    """Test validating multiple tags."""
    tags = ["project", "todo", "urgent"]
    mock_validator.validate_tags.return_value = {
        "success": True,
        "valid": True,
        "invalid_tags": []
    }
    
    result = tag_manager.validate_tags(tags)
    assert result["success"] is True
    assert result["valid"] is True
    assert len(result["invalid_tags"]) == 0

def test_add_tag_to_note(tag_manager, mock_storage):
    """Test adding a tag to a note."""
    note_path = "test/note.md"
    tag = "project"
    mock_storage.add_tag_to_note.return_value = {
        "success": True,
        "added": True
    }
    
    result = tag_manager.add_tag_to_note(note_path, tag)
    assert result["success"] is True
    assert result["added"] is True

def test_remove_tag_from_note(tag_manager, mock_storage):
    """Test removing a tag from a note."""
    note_path = "test/note.md"
    tag = "project"
    mock_storage.remove_tag_from_note.return_value = {
        "success": True,
        "removed": True
    }
    
    result = tag_manager.remove_tag_from_note(note_path, tag)
    assert result["success"] is True
    assert result["removed"] is True

def test_get_notes_with_tag(tag_manager, mock_storage):
    """Test getting all notes with a specific tag."""
    tag = "project"
    mock_storage.get_notes_with_tag.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md"]
    }
    
    result = tag_manager.get_notes_with_tag(tag)
    assert result["success"] is True
    assert isinstance(result["notes"], list)
    assert len(result["notes"]) == 2

def test_error_handling_invalid_tag(tag_manager, mock_validator):
    """Test error handling for invalid tag."""
    tag = "invalid#tag"
    mock_validator.validate_tag.return_value = {
        "success": True,
        "valid": False,
        "error": "Invalid tag format"
    }
    
    result = tag_manager.add_tag(tag)
    assert result["success"] is False
    assert "error" in result 
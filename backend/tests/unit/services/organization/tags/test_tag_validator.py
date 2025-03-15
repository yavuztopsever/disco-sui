import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.organization.tags.tag_validator import TagValidator

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def tag_validator(mock_context, mock_storage):
    return TagValidator(
        context=mock_context,
        storage=mock_storage
    )

def test_tag_validator_initialization(tag_validator):
    """Test tag validator initialization."""
    assert tag_validator is not None
    assert tag_validator.storage is not None

def test_validate_tag_format(tag_validator):
    """Test tag format validation."""
    # Test valid tag
    result = tag_validator.validate_tag_format("project-123")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid tag (spaces)
    result = tag_validator.validate_tag_format("invalid tag")
    assert result["success"] is True
    assert result["valid"] is False
    assert "spaces" in result["errors"][0].lower()
    
    # Test invalid tag (special characters)
    result = tag_validator.validate_tag_format("tag@#$")
    assert result["success"] is True
    assert result["valid"] is False
    assert "special characters" in result["errors"][0].lower()

def test_validate_tag_length(tag_validator):
    """Test tag length validation."""
    # Test valid length
    result = tag_validator.validate_tag_length("project")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test too short
    result = tag_validator.validate_tag_length("a")
    assert result["success"] is True
    assert result["valid"] is False
    assert "length" in result["errors"][0].lower()
    
    # Test too long
    long_tag = "a" * 51
    result = tag_validator.validate_tag_length(long_tag)
    assert result["success"] is True
    assert result["valid"] is False
    assert "length" in result["errors"][0].lower()

def test_check_tag_exists(tag_validator, mock_storage):
    """Test checking if tag exists."""
    tag = "project"
    mock_storage.tag_exists.return_value = {"success": True, "exists": True}
    
    result = tag_validator.check_tag_exists(tag)
    assert result["success"] is True
    assert result["exists"] is True

def test_validate_tag_category(tag_validator):
    """Test tag category validation."""
    # Test valid category
    result = tag_validator.validate_tag_category("status")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid category
    result = tag_validator.validate_tag_category("invalid@category")
    assert result["success"] is True
    assert result["valid"] is False
    assert "category" in result["errors"][0].lower()

def test_validate_tag_hierarchy(tag_validator):
    """Test tag hierarchy validation."""
    # Test valid hierarchy
    result = tag_validator.validate_tag_hierarchy("project/subtask")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid hierarchy (too deep)
    result = tag_validator.validate_tag_hierarchy("a/b/c/d/e/f")
    assert result["success"] is True
    assert result["valid"] is False
    assert "hierarchy" in result["errors"][0].lower()

def test_batch_validate_tags(tag_validator):
    """Test batch tag validation."""
    tags = ["project", "todo", "invalid tag", "task-1"]
    
    result = tag_validator.batch_validate_tags(tags)
    assert result["success"] is True
    assert "valid_tags" in result
    assert "invalid_tags" in result
    assert len(result["valid_tags"]) == 2
    assert len(result["invalid_tags"]) == 2

def test_validate_tag_relationships(tag_validator, mock_storage):
    """Test tag relationship validation."""
    parent_tag = "project"
    child_tag = "subtask"
    mock_storage.check_tag_relationship.return_value = {
        "success": True,
        "valid": True
    }
    
    result = tag_validator.validate_tag_relationship(parent_tag, child_tag)
    assert result["success"] is True
    assert result["valid"] is True

def test_validate_tag_uniqueness(tag_validator, mock_storage):
    """Test tag uniqueness validation."""
    tag = "project"
    mock_storage.tag_exists.return_value = {"success": True, "exists": False}
    
    result = tag_validator.validate_tag_uniqueness(tag)
    assert result["success"] is True
    assert result["valid"] is True

def test_error_handling(tag_validator, mock_storage):
    """Test error handling."""
    mock_storage.tag_exists.side_effect = Exception("Database error")
    
    result = tag_validator.check_tag_exists("project")
    assert result["success"] is False
    assert "error" in result

def test_validate_tag_pattern(tag_validator):
    """Test tag pattern validation."""
    # Test valid pattern
    result = tag_validator.validate_tag_pattern("project-*")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid pattern
    result = tag_validator.validate_tag_pattern("project[invalid]")
    assert result["success"] is True
    assert result["valid"] is False
    assert "pattern" in result["errors"][0].lower()

def test_validate_tag_reserved_words(tag_validator):
    """Test reserved words validation."""
    # Test non-reserved word
    result = tag_validator.validate_reserved_words("project")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test reserved word
    result = tag_validator.validate_reserved_words("tag")
    assert result["success"] is True
    assert result["valid"] is False
    assert "reserved" in result["errors"][0].lower() 
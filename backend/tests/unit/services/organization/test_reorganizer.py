import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.services.organization.reorganizer import Reorganizer

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def mock_analyzer():
    return MagicMock()

@pytest.fixture
def reorganizer(mock_context, mock_storage, mock_analyzer):
    return Reorganizer(
        context=mock_context,
        storage=mock_storage,
        analyzer=mock_analyzer
    )

def test_reorganizer_initialization(reorganizer):
    """Test reorganizer initialization."""
    assert reorganizer is not None
    assert reorganizer.storage is not None
    assert reorganizer.analyzer is not None

def test_analyze_vault_structure(reorganizer, mock_storage):
    """Test vault structure analysis."""
    vault_path = "test/vault"
    mock_storage.list_files.return_value = {
        "success": True,
        "files": [
            "projects/note1.md",
            "archive/note2.md",
            "daily/note3.md"
        ]
    }
    
    result = reorganizer.analyze_structure(vault_path)
    assert result["success"] is True
    assert "structure" in result
    assert isinstance(result["structure"], dict)

def test_suggest_reorganization(reorganizer, mock_analyzer):
    """Test reorganization suggestions."""
    vault_path = "test/vault"
    mock_analyzer.analyze_organization.return_value = {
        "success": True,
        "suggestions": [
            {
                "type": "move",
                "source": "misc/project.md",
                "target": "projects/active/project.md",
                "reason": "Project note in misc folder"
            }
        ]
    }
    
    result = reorganizer.suggest_reorganization(vault_path)
    assert result["success"] is True
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0

def test_apply_changes(reorganizer, mock_storage):
    """Test applying changes."""
    changes = [
        {
            "type": "move",
            "source": "old/path.md",
            "target": "new/path.md"
        },
        {
            "type": "rename",
            "source": "old_name.md",
            "target": "new_name.md"
        }
    ]
    mock_storage.move_file.return_value = {"success": True}
    mock_storage.rename_file.return_value = {"success": True}
    
    result = reorganizer.apply_changes(changes)
    assert result["success"] is True
    assert result["applied"] > 0

def test_analyze_note_content(reorganizer, mock_analyzer):
    """Test note content analysis."""
    note_path = "test/note.md"
    mock_analyzer.analyze_content.return_value = {
        "success": True,
        "content": {
            "tags": ["project", "todo"],
            "links": ["note1.md", "note2.md"],
            "headers": ["Title", "Section 1", "Section 2"]
        }
    }
    
    result = reorganizer.analyze_note_content(note_path)
    assert result["success"] is True
    assert "content" in result
    assert "tags" in result["content"]

def test_create_organization_plan(reorganizer):
    """Test organization plan creation."""
    structure = {
        "projects": {"active": {}, "archive": {}},
        "daily": {},
        "resources": {}
    }
    
    result = reorganizer.create_organization_plan(structure)
    assert result["success"] is True
    assert "plan" in result
    assert isinstance(result["plan"], dict)

def test_validate_changes(reorganizer):
    """Test changes validation."""
    changes = [
        {
            "type": "move",
            "source": "old/path.md",
            "target": "new/path.md"
        }
    ]
    
    result = reorganizer.validate_changes(changes)
    assert result["success"] is True
    assert result["valid"] is True

def test_error_handling_invalid_path(reorganizer, mock_storage):
    """Test error handling for invalid path."""
    mock_storage.list_files.side_effect = FileNotFoundError()
    
    result = reorganizer.analyze_structure("invalid/path")
    assert result["success"] is False
    assert "error" in result

def test_analyze_tags(reorganizer, mock_analyzer):
    """Test tag analysis."""
    tags = ["project", "todo", "urgent"]
    mock_analyzer.analyze_tags.return_value = {
        "success": True,
        "analysis": {
            "count": 3,
            "categories": ["workflow", "status"],
            "usage": {"project": 5, "todo": 3, "urgent": 1}
        }
    }
    
    result = reorganizer.analyze_tags(tags)
    assert result["success"] is True
    assert "analysis" in result
    assert "categories" in result["analysis"]

def test_reorganize_by_category(reorganizer):
    """Test reorganization by category."""
    notes = [
        {"path": "note1.md", "category": "project"},
        {"path": "note2.md", "category": "archive"},
        {"path": "note3.md", "category": "daily"}
    ]
    
    result = reorganizer.reorganize_by_category(notes)
    assert result["success"] is True
    assert "categories" in result
    assert len(result["categories"]) > 0

def test_analyze_folder_structure(reorganizer, mock_storage):
    """Test folder structure analysis."""
    folder_path = "test/folder"
    mock_storage.get_folder_structure.return_value = {
        "success": True,
        "structure": {
            "depth": 3,
            "folders": ["subfolder1", "subfolder2"],
            "files": ["note1.md", "note2.md"]
        }
    }
    
    result = reorganizer.analyze_folder_structure(folder_path)
    assert result["success"] is True
    assert "structure" in result
    assert "depth" in result["structure"]

def test_batch_reorganization(reorganizer):
    """Test batch reorganization."""
    paths = ["note1.md", "note2.md", "note3.md"]
    
    result = reorganizer.batch_reorganize(paths)
    assert result["success"] is True
    assert "reorganized" in result
    assert isinstance(result["reorganized"], list) 
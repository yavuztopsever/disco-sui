import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.organization.organization_service import OrganizationService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_reorganizer():
    return MagicMock()

@pytest.fixture
def mock_tag_manager():
    return MagicMock()

@pytest.fixture
def organization_service(mock_context, mock_reorganizer, mock_tag_manager):
    service = OrganizationService(context=mock_context)
    service._reorganizer = mock_reorganizer
    service._tag_manager = mock_tag_manager
    return service

def test_service_initialization(organization_service):
    """Test organization service initialization."""
    assert organization_service is not None
    assert organization_service.context is not None
    assert organization_service._reorganizer is not None
    assert organization_service._tag_manager is not None

def test_organize_notes(organization_service, mock_reorganizer):
    """Test organizing notes."""
    mock_reorganizer.organize_notes.return_value = {
        "success": True,
        "organized": 5,
        "details": ["note1.md", "note2.md"]
    }
    
    result = organization_service.organize_notes()
    assert result["success"] is True
    assert result["organized"] == 5
    assert len(result["details"]) == 2
    mock_reorganizer.organize_notes.assert_called_once()

def test_reorganize_by_tags(organization_service, mock_reorganizer):
    """Test reorganizing notes by tags."""
    mock_reorganizer.reorganize_by_tags.return_value = {
        "success": True,
        "reorganized": 3,
        "tags": ["tag1", "tag2"]
    }
    
    result = organization_service.reorganize_by_tags(["tag1", "tag2"])
    assert result["success"] is True
    assert result["reorganized"] == 3
    assert len(result["tags"]) == 2
    mock_reorganizer.reorganize_by_tags.assert_called_once_with(["tag1", "tag2"])

def test_reorganize_by_date(organization_service, mock_reorganizer):
    """Test reorganizing notes by date."""
    mock_reorganizer.reorganize_by_date.return_value = {
        "success": True,
        "reorganized": 4,
        "date_range": "2024-01-01 to 2024-03-14"
    }
    
    result = organization_service.reorganize_by_date("2024-01-01", "2024-03-14")
    assert result["success"] is True
    assert result["reorganized"] == 4
    assert "date_range" in result
    mock_reorganizer.reorganize_by_date.assert_called_once_with("2024-01-01", "2024-03-14")

def test_reorganize_by_hierarchy(organization_service, mock_reorganizer):
    """Test reorganizing notes by hierarchy."""
    mock_reorganizer.reorganize_by_hierarchy.return_value = {
        "success": True,
        "reorganized": 6,
        "hierarchy_levels": 3
    }
    
    result = organization_service.reorganize_by_hierarchy()
    assert result["success"] is True
    assert result["reorganized"] == 6
    assert result["hierarchy_levels"] == 3
    mock_reorganizer.reorganize_by_hierarchy.assert_called_once()

def test_add_tag(organization_service, mock_tag_manager):
    """Test adding a tag."""
    mock_tag_manager.add_tag.return_value = {
        "success": True,
        "tag": "new_tag",
        "added": True
    }
    
    result = organization_service.add_tag("new_tag")
    assert result["success"] is True
    assert result["tag"] == "new_tag"
    assert result["added"] is True
    mock_tag_manager.add_tag.assert_called_once_with("new_tag")

def test_remove_tag(organization_service, mock_tag_manager):
    """Test removing a tag."""
    mock_tag_manager.remove_tag.return_value = {
        "success": True,
        "tag": "old_tag",
        "removed": True
    }
    
    result = organization_service.remove_tag("old_tag")
    assert result["success"] is True
    assert result["tag"] == "old_tag"
    assert result["removed"] is True
    mock_tag_manager.remove_tag.assert_called_once_with("old_tag")

def test_list_tags(organization_service, mock_tag_manager):
    """Test listing tags."""
    mock_tag_manager.list_tags.return_value = {
        "success": True,
        "tags": ["tag1", "tag2", "tag3"],
        "count": 3
    }
    
    result = organization_service.list_tags()
    assert result["success"] is True
    assert len(result["tags"]) == 3
    assert result["count"] == 3
    mock_tag_manager.list_tags.assert_called_once()

def test_update_tag(organization_service, mock_tag_manager):
    """Test updating a tag."""
    mock_tag_manager.update_tag.return_value = {
        "success": True,
        "old_tag": "old_tag",
        "new_tag": "new_tag",
        "updated": True
    }
    
    result = organization_service.update_tag("old_tag", "new_tag")
    assert result["success"] is True
    assert result["old_tag"] == "old_tag"
    assert result["new_tag"] == "new_tag"
    assert result["updated"] is True
    mock_tag_manager.update_tag.assert_called_once_with("old_tag", "new_tag")

def test_get_tag_statistics(organization_service, mock_tag_manager):
    """Test getting tag statistics."""
    mock_tag_manager.get_statistics.return_value = {
        "success": True,
        "total_tags": 10,
        "most_used": ["tag1", "tag2"],
        "least_used": ["tag9", "tag10"]
    }
    
    result = organization_service.get_tag_statistics()
    assert result["success"] is True
    assert result["total_tags"] == 10
    assert len(result["most_used"]) == 2
    assert len(result["least_used"]) == 2
    mock_tag_manager.get_statistics.assert_called_once()

def test_error_handling_organize(organization_service, mock_reorganizer):
    """Test error handling during organization."""
    mock_reorganizer.organize_notes.side_effect = Exception("Organization error")
    
    result = organization_service.organize_notes()
    assert result["success"] is False
    assert "error" in result

def test_error_handling_tag_operation(organization_service, mock_tag_manager):
    """Test error handling during tag operations."""
    mock_tag_manager.add_tag.side_effect = Exception("Tag error")
    
    result = organization_service.add_tag("new_tag")
    assert result["success"] is False
    assert "error" in result

def test_batch_tag_operations(organization_service, mock_tag_manager):
    """Test batch tag operations."""
    mock_tag_manager.batch_add_tags.return_value = {
        "success": True,
        "added": ["tag1", "tag2"],
        "failed": []
    }
    
    result = organization_service.batch_add_tags(["tag1", "tag2"])
    assert result["success"] is True
    assert len(result["added"]) == 2
    assert len(result["failed"]) == 0
    mock_tag_manager.batch_add_tags.assert_called_once_with(["tag1", "tag2"])

def test_get_organization_status(organization_service, mock_reorganizer):
    """Test getting organization status."""
    mock_reorganizer.get_status.return_value = {
        "success": True,
        "status": "idle",
        "last_organization": "2024-03-14 12:00:00",
        "pending_tasks": 0
    }
    
    result = organization_service.get_status()
    assert result["success"] is True
    assert result["status"] == "idle"
    assert "last_organization" in result
    assert result["pending_tasks"] == 0
    mock_reorganizer.get_status.assert_called_once()

def test_validate_organization_rules(organization_service, mock_reorganizer):
    """Test validating organization rules."""
    rules = {
        "tag_based": True,
        "date_based": False,
        "hierarchy": True
    }
    mock_reorganizer.validate_rules.return_value = {
        "success": True,
        "valid": True,
        "rules": rules
    }
    
    result = organization_service.validate_rules(rules)
    assert result["success"] is True
    assert result["valid"] is True
    assert result["rules"] == rules
    mock_reorganizer.validate_rules.assert_called_once_with(rules)

def test_get_organization_config(organization_service):
    """Test getting organization configuration."""
    result = organization_service.get_config()
    assert result["success"] is True
    assert "config" in result
    assert isinstance(result["config"], dict)

def test_update_organization_config(organization_service):
    """Test updating organization configuration."""
    config_update = {
        "auto_organize": True,
        "organization_interval": 3600
    }
    
    result = organization_service.update_config(config_update)
    assert result["success"] is True
    assert result["config"] == config_update

def test_analyze_vault_structure(organization_service, mock_reorganizer):
    """Test vault structure analysis."""
    vault_path = "test/vault"
    mock_reorganizer.analyze_structure.return_value = {
        "success": True,
        "structure": {
            "folders": 10,
            "notes": 50,
            "depth": 3,
            "categories": ["projects", "archive", "daily"]
        }
    }
    
    result = organization_service.analyze_vault_structure(vault_path)
    assert result["success"] is True
    assert "structure" in result
    assert "folders" in result["structure"]
    mock_reorganizer.analyze_structure.assert_called_with(vault_path)

def test_suggest_reorganization(organization_service, mock_reorganizer):
    """Test reorganization suggestions."""
    vault_path = "test/vault"
    mock_reorganizer.suggest_reorganization.return_value = {
        "success": True,
        "suggestions": [
            {"type": "move", "source": "old/path", "target": "new/path"},
            {"type": "rename", "source": "old_name", "target": "new_name"}
        ]
    }
    
    result = organization_service.suggest_reorganization(vault_path)
    assert result["success"] is True
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0

def test_apply_reorganization(organization_service, mock_reorganizer):
    """Test applying reorganization."""
    changes = [
        {"type": "move", "source": "old/path", "target": "new/path"},
        {"type": "rename", "source": "old_name", "target": "new_name"}
    ]
    mock_reorganizer.apply_changes.return_value = {
        "success": True,
        "applied": 2,
        "failed": 0
    }
    
    result = organization_service.apply_reorganization(changes)
    assert result["success"] is True
    assert result["applied"] == 2
    assert result["failed"] == 0

def test_analyze_note_organization(organization_service, mock_reorganizer):
    """Test note organization analysis."""
    note_path = "test/note.md"
    mock_reorganizer.analyze_note.return_value = {
        "success": True,
        "analysis": {
            "tags": ["project", "todo"],
            "links": 5,
            "category": "projects"
        }
    }
    
    result = organization_service.analyze_note_organization(note_path)
    assert result["success"] is True
    assert "analysis" in result
    assert "tags" in result["analysis"]

def test_create_folder_structure(organization_service, mock_reorganizer):
    """Test folder structure creation."""
    structure = {
        "projects": {"active": {}, "archive": {}},
        "daily": {},
        "resources": {}
    }
    mock_reorganizer.create_folders.return_value = {
        "success": True,
        "created": 5
    }
    
    result = organization_service.create_folder_structure(structure)
    assert result["success"] is True
    assert result["created"] == 5

def test_tag_management(organization_service, mock_reorganizer):
    """Test tag management."""
    tags = ["project", "todo", "urgent"]
    mock_reorganizer.manage_tags.return_value = {
        "success": True,
        "added": 3,
        "existing": 0
    }
    
    result = organization_service.manage_tags(tags)
    assert result["success"] is True
    assert result["added"] == 3

def test_error_handling(organization_service, mock_reorganizer):
    """Test error handling."""
    mock_reorganizer.analyze_structure.side_effect = Exception("Test error")
    
    result = organization_service.analyze_vault_structure("test/vault")
    assert result["success"] is False
    assert "error" in result

def test_move_note(organization_service, mock_reorganizer):
    """Test note movement."""
    source = "old/path/note.md"
    target = "new/path/note.md"
    mock_reorganizer.move_note.return_value = {
        "success": True,
        "new_path": target
    }
    
    result = organization_service.move_note(source, target)
    assert result["success"] is True
    assert result["new_path"] == target

def test_rename_folder(organization_service, mock_reorganizer):
    """Test folder renaming."""
    old_name = "old_folder"
    new_name = "new_folder"
    mock_reorganizer.rename_folder.return_value = {
        "success": True,
        "new_path": f"vault/{new_name}"
    }
    
    result = organization_service.rename_folder(old_name, new_name)
    assert result["success"] is True
    assert new_name in result["new_path"]

def test_analyze_links(organization_service, mock_reorganizer):
    """Test link analysis."""
    note_path = "test/note.md"
    mock_reorganizer.analyze_links.return_value = {
        "success": True,
        "links": {
            "internal": 5,
            "external": 3,
            "broken": 1
        }
    }
    
    result = organization_service.analyze_links(note_path)
    assert result["success"] is True
    assert "links" in result
    assert all(k in result["links"] for k in ["internal", "external", "broken"])

def test_batch_organization(organization_service, mock_reorganizer):
    """Test batch organization."""
    paths = ["note1.md", "note2.md", "note3.md"]
    mock_reorganizer.batch_organize.return_value = {
        "success": True,
        "organized": 3,
        "skipped": 0
    }
    
    result = organization_service.batch_organize(paths)
    assert result["success"] is True
    assert result["organized"] == len(paths) 
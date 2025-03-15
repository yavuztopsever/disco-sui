import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.content.manipulation.service import ManipulationService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_note_manager():
    return MagicMock()

@pytest.fixture
def mock_template_scheduler():
    return MagicMock()

@pytest.fixture
def manipulation_service(mock_context, mock_note_manager, mock_template_scheduler):
    return ManipulationService(
        context=mock_context,
        note_manager=mock_note_manager,
        template_scheduler=mock_template_scheduler
    )

def test_service_initialization(manipulation_service):
    """Test service initialization."""
    assert manipulation_service is not None
    assert manipulation_service.note_manager is not None
    assert manipulation_service.template_scheduler is not None

def test_start_service(manipulation_service, mock_template_scheduler):
    """Test starting the service."""
    mock_template_scheduler.start.return_value = {
        "success": True,
        "started": True
    }
    
    result = manipulation_service.start()
    assert result["success"] is True
    assert result["started"] is True
    mock_template_scheduler.start.assert_called_once()

def test_stop_service(manipulation_service, mock_template_scheduler):
    """Test stopping the service."""
    mock_template_scheduler.stop.return_value = {
        "success": True,
        "stopped": True
    }
    
    result = manipulation_service.stop()
    assert result["success"] is True
    assert result["stopped"] is True
    mock_template_scheduler.stop.assert_called_once()

def test_get_service_status(manipulation_service, mock_template_scheduler):
    """Test getting service status."""
    mock_template_scheduler.get_status.return_value = {
        "success": True,
        "status": "running",
        "active_schedules": 2
    }
    
    result = manipulation_service.get_status()
    assert result["success"] is True
    assert "status" in result
    assert "active_schedules" in result

def test_create_note(manipulation_service, mock_note_manager):
    """Test creating a note."""
    title = "Test Note"
    content = "# Test Content"
    mock_note_manager.create_note.return_value = {
        "success": True,
        "path": "notes/test_note.md"
    }
    
    result = manipulation_service.create_note(title, content)
    assert result["success"] is True
    assert "path" in result
    mock_note_manager.create_note.assert_called_with(title, content)

def test_update_note(manipulation_service, mock_note_manager):
    """Test updating a note."""
    note_path = "notes/test_note.md"
    new_content = "# Updated Content"
    mock_note_manager.update_note.return_value = {
        "success": True,
        "path": note_path
    }
    
    result = manipulation_service.update_note(note_path, new_content)
    assert result["success"] is True
    assert result["path"] == note_path

def test_delete_note(manipulation_service, mock_note_manager):
    """Test deleting a note."""
    note_path = "notes/test_note.md"
    mock_note_manager.delete_note.return_value = {
        "success": True,
        "deleted": True
    }
    
    result = manipulation_service.delete_note(note_path)
    assert result["success"] is True
    assert result["deleted"] is True

def test_schedule_template(manipulation_service, mock_template_scheduler):
    """Test scheduling a template."""
    template_path = "templates/daily.md"
    schedule = {
        "type": "daily",
        "time": "09:00"
    }
    mock_template_scheduler.schedule_template.return_value = {
        "success": True,
        "schedule_id": "test_schedule_123"
    }
    
    result = manipulation_service.schedule_template(template_path, schedule)
    assert result["success"] is True
    assert "schedule_id" in result

def test_unschedule_template(manipulation_service, mock_template_scheduler):
    """Test unscheduling a template."""
    schedule_id = "test_schedule_123"
    mock_template_scheduler.unschedule_template.return_value = {
        "success": True,
        "unscheduled": True
    }
    
    result = manipulation_service.unschedule_template(schedule_id)
    assert result["success"] is True
    assert result["unscheduled"] is True

def test_list_schedules(manipulation_service, mock_template_scheduler):
    """Test listing template schedules."""
    mock_template_scheduler.list_schedules.return_value = {
        "success": True,
        "schedules": [
            {
                "id": "schedule1",
                "template": "daily.md",
                "type": "daily"
            },
            {
                "id": "schedule2",
                "template": "weekly.md",
                "type": "weekly"
            }
        ]
    }
    
    result = manipulation_service.list_schedules()
    assert result["success"] is True
    assert len(result["schedules"]) == 2

def test_error_handling(manipulation_service, mock_note_manager):
    """Test error handling."""
    mock_note_manager.create_note.side_effect = Exception("Test error")
    
    result = manipulation_service.create_note("Test", "Content")
    assert result["success"] is False
    assert "error" in result

def test_batch_operation(manipulation_service, mock_note_manager):
    """Test batch note operation."""
    operations = [
        {"type": "create", "title": "Note 1", "content": "Content 1"},
        {"type": "create", "title": "Note 2", "content": "Content 2"}
    ]
    mock_note_manager.batch_operation.return_value = {
        "success": True,
        "results": [
            {"success": True, "path": "notes/note1.md"},
            {"success": True, "path": "notes/note2.md"}
        ]
    }
    
    result = manipulation_service.batch_operation(operations)
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert all(r["success"] for r in result["results"])

def test_validate_schedule(manipulation_service, mock_template_scheduler):
    """Test schedule validation."""
    schedule = {
        "type": "daily",
        "time": "09:00"
    }
    mock_template_scheduler.validate_schedule.return_value = {
        "success": True,
        "valid": True
    }
    
    result = manipulation_service.validate_schedule(schedule)
    assert result["success"] is True
    assert result["valid"] is True

def test_get_schedule_status(manipulation_service, mock_template_scheduler):
    """Test getting schedule status."""
    schedule_id = "test_schedule_123"
    mock_template_scheduler.get_schedule_status.return_value = {
        "success": True,
        "status": "active",
        "last_execution": "2024-01-01T09:00:00",
        "next_execution": "2024-01-02T09:00:00"
    }
    
    result = manipulation_service.get_schedule_status(schedule_id)
    assert result["success"] is True
    assert "status" in result
    assert "last_execution" in result
    assert "next_execution" in result 
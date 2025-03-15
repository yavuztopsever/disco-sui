import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.services.content.manipulation.template_scheduler import TemplateScheduler

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
def template_scheduler(mock_context, mock_storage, mock_processor):
    return TemplateScheduler(
        context=mock_context,
        storage=mock_storage,
        processor=mock_processor
    )

def test_template_scheduler_initialization(template_scheduler):
    """Test template scheduler initialization."""
    assert template_scheduler is not None
    assert template_scheduler.storage is not None
    assert template_scheduler.processor is not None

def test_schedule_template(template_scheduler, mock_storage):
    """Test scheduling a template."""
    template_path = "templates/daily.md"
    schedule = {
        "type": "daily",
        "time": "09:00",
        "target_folder": "notes/daily"
    }
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "# Daily Template\nDate: {{date}}"
    }
    
    result = template_scheduler.schedule_template(template_path, schedule)
    assert result["success"] is True
    assert "schedule_id" in result

def test_unschedule_template(template_scheduler):
    """Test unscheduling a template."""
    schedule_id = "test_schedule_123"
    
    result = template_scheduler.unschedule_template(schedule_id)
    assert result["success"] is True
    assert result["unscheduled"] is True

def test_list_schedules(template_scheduler):
    """Test listing template schedules."""
    mock_schedules = [
        {
            "id": "schedule1",
            "template": "templates/daily.md",
            "type": "daily",
            "time": "09:00"
        },
        {
            "id": "schedule2",
            "template": "templates/weekly.md",
            "type": "weekly",
            "day": "Monday",
            "time": "08:00"
        }
    ]
    template_scheduler._schedules = mock_schedules
    
    result = template_scheduler.list_schedules()
    assert result["success"] is True
    assert len(result["schedules"]) == 2

def test_process_template(template_scheduler, mock_processor):
    """Test processing a template."""
    template_content = "# {{title}}\nDate: {{date}}"
    variables = {
        "title": "Test Note",
        "date": "2024-01-01"
    }
    mock_processor.process_template.return_value = {
        "success": True,
        "content": "# Test Note\nDate: 2024-01-01"
    }
    
    result = template_scheduler.process_template(template_content, variables)
    assert result["success"] is True
    assert "content" in result

def test_create_scheduled_note(template_scheduler, mock_storage, mock_processor):
    """Test creating a scheduled note."""
    schedule = {
        "template": "templates/daily.md",
        "target_folder": "notes/daily",
        "variables": {
            "title": "Daily Note",
            "date": "2024-01-01"
        }
    }
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "# {{title}}\nDate: {{date}}"
    }
    mock_processor.process_template.return_value = {
        "success": True,
        "content": "# Daily Note\nDate: 2024-01-01"
    }
    mock_storage.create_note.return_value = {
        "success": True,
        "path": "notes/daily/2024-01-01.md"
    }
    
    result = template_scheduler.create_scheduled_note(schedule)
    assert result["success"] is True
    assert "path" in result

def test_validate_schedule(template_scheduler):
    """Test schedule validation."""
    valid_schedule = {
        "type": "daily",
        "time": "09:00",
        "target_folder": "notes/daily"
    }
    
    result = template_scheduler.validate_schedule(valid_schedule)
    assert result["success"] is True
    assert result["valid"] is True

def test_invalid_schedule(template_scheduler):
    """Test invalid schedule validation."""
    invalid_schedule = {
        "type": "invalid",
        "time": "25:00"  # Invalid time
    }
    
    result = template_scheduler.validate_schedule(invalid_schedule)
    assert result["success"] is True
    assert result["valid"] is False
    assert len(result["errors"]) > 0

def test_get_next_execution(template_scheduler):
    """Test getting next execution time."""
    schedule = {
        "type": "daily",
        "time": "09:00"
    }
    now = datetime.now()
    
    result = template_scheduler.get_next_execution(schedule)
    assert result["success"] is True
    assert "next_execution" in result
    next_time = datetime.fromisoformat(result["next_execution"])
    assert next_time > now

def test_update_schedule(template_scheduler):
    """Test updating a schedule."""
    schedule_id = "test_schedule_123"
    updates = {
        "time": "10:00",
        "target_folder": "new/folder"
    }
    
    result = template_scheduler.update_schedule(schedule_id, updates)
    assert result["success"] is True
    assert "updated_schedule" in result

def test_pause_schedule(template_scheduler):
    """Test pausing a schedule."""
    schedule_id = "test_schedule_123"
    
    result = template_scheduler.pause_schedule(schedule_id)
    assert result["success"] is True
    assert result["paused"] is True

def test_resume_schedule(template_scheduler):
    """Test resuming a schedule."""
    schedule_id = "test_schedule_123"
    
    result = template_scheduler.resume_schedule(schedule_id)
    assert result["success"] is True
    assert result["resumed"] is True

def test_get_schedule_status(template_scheduler):
    """Test getting schedule status."""
    schedule_id = "test_schedule_123"
    
    result = template_scheduler.get_schedule_status(schedule_id)
    assert result["success"] is True
    assert "status" in result
    assert "last_execution" in result
    assert "next_execution" in result

def test_error_handling(template_scheduler, mock_storage):
    """Test error handling."""
    mock_storage.read_note.side_effect = Exception("Test error")
    
    result = template_scheduler.schedule_template("invalid/path.md", {})
    assert result["success"] is False
    assert "error" in result

def test_batch_schedule(template_scheduler):
    """Test batch scheduling."""
    schedules = [
        {
            "template": "templates/daily.md",
            "schedule": {
                "type": "daily",
                "time": "09:00"
            }
        },
        {
            "template": "templates/weekly.md",
            "schedule": {
                "type": "weekly",
                "day": "Monday",
                "time": "08:00"
            }
        }
    ]
    
    result = template_scheduler.batch_schedule(schedules)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == len(schedules) 
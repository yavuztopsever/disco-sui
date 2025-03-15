"""Integration tests for task management flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime, timedelta

from src.core.config import Settings
from src.services.task.task_manager import TaskManager
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with tasks."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create notes with various tasks
    notes = {
        "projects/project_tasks.md": """# Project Tasks

## Development Tasks
- [ ] Setup development environment
- [x] Create project structure
- [ ] Implement core features
  - [ ] User authentication
  - [ ] Data processing
  - [ ] API endpoints
- [ ] Write documentation

## Testing Tasks
- [ ] Write unit tests
- [ ] Setup CI/CD pipeline
- [x] Configure test environment

Due Date: 2024-03-01
Priority: High""",
        
        "daily/todo.md": """# Daily Tasks
Date: 2024-01-17

## Morning
- [x] Check emails
- [ ] Team standup meeting
- [ ] Review pull requests

## Afternoon
- [ ] Project planning meeting
- [ ] Documentation review
- [ ] Code review

Priority: Medium""",
        
        "personal/goals.md": """# Personal Goals

## Learning
- [ ] Complete Python course
- [ ] Study machine learning
- [x] Read documentation

## Projects
- [ ] Portfolio website
- [ ] Blog posts
  - [x] Draft outline
  - [ ] Write content
  - [ ] Review and edit

Due Date: 2024-06-30"""
    }
    
    for filepath, content in notes.items():
        file_path = vault_path / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    # Create necessary directories
    task_db_path = tmp_path / "tasks"
    task_db_path.mkdir()
    
    return {
        "vault_path": test_notes,
        "task_db_path": task_db_path
    }

@pytest.mark.asyncio
async def test_task_extraction(test_environment):
    """Test task extraction from notes."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Extract tasks
    result = await task_manager.extract_tasks()
    
    # Verify task extraction
    assert result.success is True
    assert len(result.tasks) > 0
    assert result.total_tasks > 10
    assert result.completed_tasks >= 4
    
    # Verify task structure
    project_tasks = [task for task in result.tasks 
                    if task.source_file == "projects/project_tasks.md"]
    assert any(task.text == "Setup development environment" for task in project_tasks)
    assert any(task.is_completed for task in project_tasks)

@pytest.mark.asyncio
async def test_task_organization(test_environment):
    """Test task organization and categorization."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Organize tasks
    result = await task_manager.organize_tasks()
    
    # Verify organization
    assert result.success is True
    assert "projects" in result.categories
    assert "daily" in result.categories
    assert "personal" in result.categories
    
    # Verify category contents
    assert len(result.categories["projects"]) > 0
    assert all(task.category == "projects" 
              for task in result.categories["projects"])

@pytest.mark.asyncio
async def test_task_prioritization(test_environment):
    """Test task prioritization system."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Prioritize tasks
    result = await task_manager.prioritize_tasks()
    
    # Verify prioritization
    assert result.success is True
    assert len(result.high_priority) > 0
    assert len(result.medium_priority) > 0
    
    # Verify priority assignment
    assert all(task.priority == "high" for task in result.high_priority)
    assert all(task.priority == "medium" for task in result.medium_priority)

@pytest.mark.asyncio
async def test_task_scheduling(test_environment):
    """Test task scheduling and due date management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Schedule tasks
    result = await task_manager.schedule_tasks()
    
    # Verify scheduling
    assert result.success is True
    assert len(result.scheduled_tasks) > 0
    
    # Verify due dates
    project_tasks = [task for task in result.scheduled_tasks 
                    if task.source_file == "projects/project_tasks.md"]
    assert any(task.due_date == "2024-03-01" for task in project_tasks)

@pytest.mark.asyncio
async def test_task_dependencies(test_environment):
    """Test task dependency management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Analyze dependencies
    result = await task_manager.analyze_dependencies()
    
    # Verify dependency analysis
    assert result.success is True
    assert len(result.dependency_graph) > 0
    
    # Verify specific dependencies
    core_features = next(task for task in result.tasks 
                        if task.text == "Implement core features")
    assert len(core_features.subtasks) == 3

@pytest.mark.asyncio
async def test_task_progress_tracking(test_environment):
    """Test task progress tracking."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Track progress
    result = await task_manager.track_progress()
    
    # Verify progress tracking
    assert result.success is True
    assert result.total_tasks > 0
    assert result.completed_percentage >= 0
    assert result.completed_percentage <= 100
    
    # Verify project progress
    project_progress = result.project_progress["projects/project_tasks.md"]
    assert project_progress.total_tasks > 0
    assert project_progress.completed_tasks >= 2

@pytest.mark.asyncio
async def test_task_notifications(test_environment):
    """Test task notification system."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    await task_manager.initialize(settings)
    
    # Get task notifications
    result = await task_manager.get_notifications()
    
    # Verify notifications
    assert result.success is True
    assert len(result.due_soon) >= 0
    assert len(result.overdue) >= 0
    
    # Verify notification content
    if result.due_soon:
        assert all(task.due_date for task in result.due_soon)
    if result.overdue:
        assert all(task.due_date for task in result.overdue)

@pytest.mark.asyncio
async def test_task_synchronization(test_environment):
    """Test task synchronization between notes and database."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TASK_DB_PATH=str(test_environment["task_db_path"])
    )
    
    task_manager = TaskManager()
    note_manager = NoteManager()
    
    await task_manager.initialize(settings)
    await note_manager.initialize(settings)
    
    # Update task in note
    note_path = test_environment["vault_path"] / "daily/todo.md"
    original_content = note_path.read_text()
    updated_content = original_content.replace("[ ] Team standup meeting", 
                                            "[x] Team standup meeting")
    note_path.write_text(updated_content)
    
    # Synchronize tasks
    result = await task_manager.synchronize_tasks()
    
    # Verify synchronization
    assert result.success is True
    assert result.updated_count > 0
    assert any(task.text == "Team standup meeting" and task.is_completed 
              for task in result.updated_tasks) 
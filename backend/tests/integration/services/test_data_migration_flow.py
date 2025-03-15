"""Integration tests for data migration flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
import json
import yaml

from src.core.config import Settings
from src.services.migration.migration_manager import MigrationManager
from src.services.migration.schema_manager import SchemaManager
from src.services.migration.data_validator import DataValidator
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_data(tmp_path) -> Path:
    """Create test data for migration testing."""
    data_path = tmp_path / "data"
    data_path.mkdir()
    
    # Create test data structures
    data = {
        "notes": {
            "old_format.md": """---
title: Old Format Note
date: 2024-01-15
tags: [test, migration]
---
# Old Format Content
This is a note in the old format.""",
            
            "nested/project_note.md": """---
type: project
status: active
priority: high
---
# Project Note
Project details in old format."""
        },
        
        "metadata": {
            "tags.json": """{
                "test": {"count": 5, "related": ["migration"]},
                "migration": {"count": 3, "related": ["test"]}
            }""",
            
            "links.yaml": """
links:
  - source: old_format.md
    target: nested/project_note.md
    type: reference
  - source: nested/project_note.md
    target: old_format.md
    type: backlink
"""
        }
    }
    
    # Create directory structure and files
    for category, files in data.items():
        category_path = data_path / category
        category_path.mkdir()
        
        for filepath, content in files.items():
            file_path = category_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
    
    return data_path

@pytest.fixture
def test_environment(tmp_path, test_data):
    """Set up test environment."""
    # Create necessary directories
    source_path = test_data
    target_path = tmp_path / "migrated_data"
    target_path.mkdir()
    backup_path = tmp_path / "backups"
    backup_path.mkdir()
    
    return {
        "source_path": source_path,
        "target_path": target_path,
        "backup_path": backup_path
    }

@pytest.mark.asyncio
async def test_schema_validation(test_environment):
    """Test schema validation for migration."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    schema_manager = SchemaManager()
    await schema_manager.initialize(settings)
    
    # Define old and new schemas
    old_schema = {
        "note": {
            "required": ["title", "date", "tags"],
            "properties": {
                "title": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
    
    new_schema = {
        "note": {
            "required": ["title", "created_at", "metadata"],
            "properties": {
                "title": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }
    }
    
    # Register schemas
    result = await schema_manager.register_schemas(old_schema, new_schema)
    
    # Verify schema registration
    assert result.success is True
    assert result.old_schema_valid is True
    assert result.new_schema_valid is True

@pytest.mark.asyncio
async def test_data_backup(test_environment):
    """Test data backup before migration."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Create backup
    backup_result = await migration_manager.create_backup()
    
    # Verify backup
    assert backup_result.success is True
    assert backup_result.backup_path is not None
    assert Path(backup_result.backup_path).exists()
    
    # Verify backup contents
    notes_backup = Path(backup_result.backup_path) / "notes"
    metadata_backup = Path(backup_result.backup_path) / "metadata"
    
    assert (notes_backup / "old_format.md").exists()
    assert (notes_backup / "nested/project_note.md").exists()
    assert (metadata_backup / "tags.json").exists()
    assert (metadata_backup / "links.yaml").exists()

@pytest.mark.asyncio
async def test_data_transformation(test_environment):
    """Test data transformation during migration."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Define transformation rules
    transform_rules = {
        "note": {
            "title": "title",  # direct mapping
            "created_at": lambda x: x["date"] + "T00:00:00Z",  # date to datetime
            "metadata": {
                "tags": "tags"  # direct mapping of tags array
            }
        }
    }
    
    # Transform data
    result = await migration_manager.transform_data(transform_rules)
    
    # Verify transformation
    assert result.success is True
    assert result.transformed_count > 0
    
    # Check transformed data
    transformed_note = Path(test_environment["target_path"]) / "notes/old_format.md"
    content = yaml.safe_load(transformed_note.read_text())
    
    assert "created_at" in content
    assert "metadata" in content
    assert "tags" in content["metadata"]

@pytest.mark.asyncio
async def test_metadata_migration(test_environment):
    """Test migration of metadata and relationships."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Migrate metadata
    result = await migration_manager.migrate_metadata()
    
    # Verify metadata migration
    assert result.success is True
    
    # Check migrated metadata
    tags_file = Path(test_environment["target_path"]) / "metadata/tags.json"
    links_file = Path(test_environment["target_path"]) / "metadata/links.yaml"
    
    assert tags_file.exists()
    assert links_file.exists()
    
    # Verify metadata content
    tags_data = json.loads(tags_file.read_text())
    assert "test" in tags_data
    assert "migration" in tags_data
    assert "related" in tags_data["test"]

@pytest.mark.asyncio
async def test_data_validation(test_environment):
    """Test validation of migrated data."""
    # Initialize services
    settings = Settings(
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    data_validator = DataValidator()
    await data_validator.initialize(settings)
    
    # Validate migrated data
    validation_result = await data_validator.validate_migrated_data()
    
    # Verify validation
    assert validation_result.success is True
    assert validation_result.valid_files > 0
    assert len(validation_result.validation_errors) == 0

@pytest.mark.asyncio
async def test_incremental_migration(test_environment):
    """Test incremental data migration."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Add new data to source
    new_note_path = test_environment["source_path"] / "notes/new_note.md"
    new_note_content = """---
title: New Note
date: 2024-01-17
tags: [test, new]
---
# New Content
This is a new note."""
    
    new_note_path.write_text(new_note_content)
    
    # Perform incremental migration
    result = await migration_manager.migrate_incremental()
    
    # Verify incremental migration
    assert result.success is True
    assert result.migrated_files == 1
    assert (test_environment["target_path"] / "notes/new_note.md").exists()

@pytest.mark.asyncio
async def test_migration_rollback(test_environment):
    """Test migration rollback functionality."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Create backup and perform migration
    await migration_manager.create_backup()
    await migration_manager.migrate_data()
    
    # Perform rollback
    rollback_result = await migration_manager.rollback_migration()
    
    # Verify rollback
    assert rollback_result.success is True
    assert rollback_result.restored_files > 0
    
    # Check restored data
    original_note = test_environment["source_path"] / "notes/old_format.md"
    restored_note = test_environment["target_path"] / "notes/old_format.md"
    
    assert original_note.read_text() == restored_note.read_text()

@pytest.mark.asyncio
async def test_migration_progress_tracking(test_environment):
    """Test migration progress tracking."""
    # Initialize services
    settings = Settings(
        SOURCE_PATH=str(test_environment["source_path"]),
        TARGET_PATH=str(test_environment["target_path"])
    )
    
    migration_manager = MigrationManager()
    await migration_manager.initialize(settings)
    
    # Register progress listener
    progress_updates = []
    
    async def progress_handler(progress):
        progress_updates.append(progress)
    
    await migration_manager.register_progress_handler(progress_handler)
    
    # Perform migration
    await migration_manager.migrate_data()
    
    # Verify progress tracking
    assert len(progress_updates) > 0
    assert progress_updates[-1].percentage == 100
    assert progress_updates[-1].completed_files > 0
    assert progress_updates[-1].total_files > 0 
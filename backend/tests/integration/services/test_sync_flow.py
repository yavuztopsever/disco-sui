"""Integration tests for synchronization flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import json
import yaml
import asyncio

from src.core.config import Settings
from src.services.sync.sync_manager import SyncManager
from src.services.sync.conflict_resolver import ConflictResolver
from src.services.sync.change_detector import ChangeDetector
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_vaults(tmp_path) -> dict:
    """Create test vaults with sample data."""
    vaults = {}
    
    # Create source and destination vaults
    for vault_name in ["source_vault", "dest_vault"]:
        vault_path = tmp_path / vault_name
        vault_path.mkdir()
        
        # Create test vault structure
        content = {
            "notes": {
                "project.md": """---
title: Project Notes
date: 2024-01-15
tags: [project, planning]
---
# Project Planning
Key project details and milestones.""",
                
                "research/analysis.md": """---
title: Research Analysis
date: 2024-01-16
tags: [research, analysis]
---
# Research Analysis
Important findings and data."""
            },
            
            "attachments": {
                "images/diagram.png": "Test image content",
                "documents/report.pdf": "Test PDF content"
            },
            
            "metadata": {
                "tags.json": """{
                    "project": {"count": 1, "related": ["planning"]},
                    "research": {"count": 1, "related": ["analysis"]}
                }""",
                
                "settings.yaml": """
theme: light
editor:
  font_size: 12
  line_numbers: true
"""
            }
        }
        
        # Create files and directories
        for category, items in content.items():
            category_path = vault_path / category
            category_path.mkdir(parents=True)
            
            for filepath, content in items.items():
                file_path = vault_path / category / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
        
        vaults[vault_name] = vault_path
    
    return vaults

@pytest.fixture
def test_environment(tmp_path, test_vaults):
    """Set up test environment."""
    # Create necessary directories
    sync_path = tmp_path / "sync"
    sync_path.mkdir()
    temp_path = tmp_path / "temp"
    temp_path.mkdir()
    
    return {
        "source_vault": test_vaults["source_vault"],
        "dest_vault": test_vaults["dest_vault"],
        "sync_path": sync_path,
        "temp_path": temp_path
    }

@pytest.mark.asyncio
async def test_initial_sync(test_environment):
    """Test initial synchronization between vaults."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"]),
        SYNC_PATH=str(test_environment["sync_path"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Perform initial sync
    sync_result = await sync_manager.perform_initial_sync()
    
    # Verify sync results
    assert sync_result.success is True
    assert sync_result.files_synced > 0
    
    # Compare vault contents
    source_files = set(p.relative_to(test_environment["source_vault"]) 
                      for p in test_environment["source_vault"].rglob("*") if p.is_file())
    dest_files = set(p.relative_to(test_environment["dest_vault"]) 
                    for p in test_environment["dest_vault"].rglob("*") if p.is_file())
    
    assert source_files == dest_files

@pytest.mark.asyncio
async def test_incremental_sync(test_environment):
    """Test incremental synchronization."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"]),
        SYNC_PATH=str(test_environment["sync_path"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Perform initial sync
    await sync_manager.perform_initial_sync()
    
    # Modify source vault
    new_note = test_environment["source_vault"] / "notes/new_note.md"
    new_note.write_text("""---
title: New Note
date: 2024-01-18
---
# New Content""")
    
    # Perform incremental sync
    sync_result = await sync_manager.perform_incremental_sync()
    
    # Verify sync results
    assert sync_result.success is True
    assert sync_result.changes_detected is True
    assert "new_note.md" in sync_result.synced_files
    assert (test_environment["dest_vault"] / "notes/new_note.md").exists()

@pytest.mark.asyncio
async def test_conflict_resolution(test_environment):
    """Test conflict resolution during sync."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"]),
        SYNC_PATH=str(test_environment["sync_path"])
    )
    
    sync_manager = SyncManager()
    conflict_resolver = ConflictResolver()
    
    await sync_manager.initialize(settings)
    await conflict_resolver.initialize(settings)
    
    # Create conflicting changes
    source_note = test_environment["source_vault"] / "notes/project.md"
    dest_note = test_environment["dest_vault"] / "notes/project.md"
    
    source_content = """---
title: Project Notes Updated
date: 2024-01-18
tags: [project, planning, updated]
---
# Project Planning
Updated project details and milestones."""
    
    dest_content = """---
title: Project Notes Modified
date: 2024-01-18
tags: [project, planning, modified]
---
# Project Planning
Modified project details and tasks."""
    
    source_note.write_text(source_content)
    dest_note.write_text(dest_content)
    
    # Perform sync with conflict resolution
    sync_result = await sync_manager.perform_sync_with_conflict_resolution()
    
    # Verify conflict resolution
    assert sync_result.success is True
    assert sync_result.conflicts_detected > 0
    assert sync_result.conflicts_resolved > 0
    
    # Check resolved file
    resolved_note = test_environment["dest_vault"] / "notes/project.md"
    assert resolved_note.exists()
    content = resolved_note.read_text()
    assert "<<<<<<< SOURCE" not in content
    assert ">>>>>>> DEST" not in content

@pytest.mark.asyncio
async def test_change_detection(test_environment):
    """Test change detection in vaults."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"])
    )
    
    change_detector = ChangeDetector()
    await change_detector.initialize(settings)
    
    # Modify source vault
    modified_note = test_environment["source_vault"] / "notes/research/analysis.md"
    modified_content = """---
title: Updated Research Analysis
date: 2024-01-18
tags: [research, analysis, updated]
---
# Updated Research Analysis
New findings and conclusions."""
    
    modified_note.write_text(modified_content)
    
    # Detect changes
    changes = await change_detector.detect_changes()
    
    # Verify change detection
    assert changes.success is True
    assert len(changes.modified_files) > 0
    assert "notes/research/analysis.md" in changes.modified_files
    assert changes.has_content_changes is True

@pytest.mark.asyncio
async def test_metadata_sync(test_environment):
    """Test synchronization of metadata."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Modify source metadata
    tags_file = test_environment["source_vault"] / "metadata/tags.json"
    updated_tags = {
        "project": {"count": 2, "related": ["planning", "development"]},
        "research": {"count": 1, "related": ["analysis"]},
        "new_tag": {"count": 1, "related": []}
    }
    
    tags_file.write_text(json.dumps(updated_tags, indent=4))
    
    # Perform metadata sync
    sync_result = await sync_manager.sync_metadata()
    
    # Verify metadata sync
    assert sync_result.success is True
    assert sync_result.metadata_synced is True
    
    # Compare metadata
    dest_tags = json.loads((test_environment["dest_vault"] / "metadata/tags.json").read_text())
    assert dest_tags == updated_tags

@pytest.mark.asyncio
async def test_sync_error_handling(test_environment):
    """Test error handling during sync."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Create invalid file in source
    invalid_file = test_environment["source_vault"] / "notes/invalid.md"
    invalid_file.write_text("Invalid YAML front matter\n---\nContent")
    
    # Perform sync with error handling
    sync_result = await sync_manager.perform_sync_with_error_handling()
    
    # Verify error handling
    assert sync_result.success is True  # Overall sync should succeed
    assert len(sync_result.errors) > 0
    assert "invalid.md" in sync_result.skipped_files
    assert sync_result.partial_sync_completed is True

@pytest.mark.asyncio
async def test_sync_progress_tracking(test_environment):
    """Test sync progress tracking."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Register progress handler
    progress_updates = []
    
    async def progress_handler(progress):
        progress_updates.append(progress)
    
    await sync_manager.register_progress_handler(progress_handler)
    
    # Perform sync
    await sync_manager.perform_full_sync()
    
    # Verify progress tracking
    assert len(progress_updates) > 0
    assert progress_updates[-1].percentage == 100
    assert progress_updates[-1].files_processed > 0
    assert progress_updates[-1].total_files > 0

@pytest.mark.asyncio
async def test_bidirectional_sync(test_environment):
    """Test bidirectional synchronization."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Make changes in both vaults
    source_note = test_environment["source_vault"] / "notes/source_new.md"
    dest_note = test_environment["dest_vault"] / "notes/dest_new.md"
    
    source_note.write_text("Source vault new content")
    dest_note.write_text("Destination vault new content")
    
    # Perform bidirectional sync
    sync_result = await sync_manager.perform_bidirectional_sync()
    
    # Verify bidirectional sync
    assert sync_result.success is True
    assert sync_result.bidirectional_sync_completed is True
    
    # Check file presence in both vaults
    assert (test_environment["source_vault"] / "notes/dest_new.md").exists()
    assert (test_environment["dest_vault"] / "notes/source_new.md").exists()

@pytest.mark.asyncio
async def test_sync_state_persistence(test_environment):
    """Test persistence of sync state."""
    # Initialize services
    settings = Settings(
        SOURCE_VAULT=str(test_environment["source_vault"]),
        DEST_VAULT=str(test_environment["dest_vault"]),
        SYNC_PATH=str(test_environment["sync_path"])
    )
    
    sync_manager = SyncManager()
    await sync_manager.initialize(settings)
    
    # Perform initial sync
    await sync_manager.perform_initial_sync()
    
    # Save sync state
    state_result = await sync_manager.save_sync_state()
    
    # Verify state persistence
    assert state_result.success is True
    assert state_result.state_saved is True
    
    # Load sync state
    load_result = await sync_manager.load_sync_state()
    
    # Verify state loading
    assert load_result.success is True
    assert load_result.state_loaded is True
    assert load_result.last_sync_time is not None 
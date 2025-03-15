"""Integration tests for note creation and management flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils
from src.services.indexing.indexer import VaultIndexer

@pytest.fixture
def test_template(tmp_path) -> Path:
    """Create a test template."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    template_content = """---
title: {{title}}
date: {{date}}
tags: {{tags}}
---

# {{title}}

## Overview
{{overview}}

## Details
{{details}}

## Related
{{related}}
"""
    
    template_path = template_dir / "test_template.md"
    template_path.write_text(template_content)
    
    return template_path

@pytest.fixture
def test_environment(tmp_path, test_template):
    """Set up test environment."""
    # Create test directories
    vault_path = tmp_path / "vault"
    backup_path = tmp_path / "backups"
    index_path = tmp_path / "index"
    
    vault_path.mkdir()
    backup_path.mkdir()
    index_path.mkdir()
    
    # Create template directory in vault
    templates_dir = vault_path / "templates"
    templates_dir.mkdir()
    shutil.copy(test_template, templates_dir / "test_template.md")
    
    return {
        "vault_path": vault_path,
        "backup_path": backup_path,
        "index_path": index_path,
        "templates_dir": templates_dir
    }

@pytest.mark.asyncio
async def test_note_creation_with_template(test_environment):
    """Test note creation using a template."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    note_manager = NoteManager()
    await note_manager.initialize(settings)
    
    # Test note creation with template
    note_data = {
        "title": "Test Note",
        "template": "test_template",
        "variables": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["test", "example"],
            "overview": "This is a test note",
            "details": "Created using a template",
            "related": ["another_note.md"]
        }
    }
    
    result = await note_manager.create_note(note_data)
    
    # Verify note creation
    assert result.success is True
    note_path = test_environment["vault_path"] / "Test Note.md"
    assert note_path.exists()
    
    # Verify note content
    content = note_path.read_text()
    assert "Test Note" in content
    assert "This is a test note" in content
    assert "Created using a template" in content
    assert "test" in content and "example" in content

@pytest.mark.asyncio
async def test_note_creation_without_template(test_environment):
    """Test note creation without a template."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    note_manager = NoteManager()
    await note_manager.initialize(settings)
    
    # Test note creation without template
    note_data = {
        "title": "Simple Note",
        "content": "# Simple Note\n\nThis is a simple note without a template."
    }
    
    result = await note_manager.create_note(note_data)
    
    # Verify note creation
    assert result.success is True
    note_path = test_environment["vault_path"] / "Simple Note.md"
    assert note_path.exists()
    assert "simple note without a template" in note_path.read_text().lower()

@pytest.mark.asyncio
async def test_note_backup_and_indexing(test_environment):
    """Test note backup and indexing process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        BACKUP_PATH=str(test_environment["backup_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    note_manager = NoteManager()
    indexer = VaultIndexer()
    
    await note_manager.initialize(settings)
    await indexer.initialize(settings)
    
    # Create a test note
    note_data = {
        "title": "Index Test Note",
        "content": "# Index Test Note\n\nThis note will be backed up and indexed."
    }
    
    result = await note_manager.create_note(note_data)
    assert result.success is True
    
    # Verify backup creation
    backup_files = list(Path(test_environment["backup_path"]).glob("*.md"))
    assert len(backup_files) > 0
    
    # Verify indexing
    index_result = await indexer.index_note(result.note_path)
    assert index_result.success is True
    assert index_result.indexed_content is not None

@pytest.mark.asyncio
async def test_note_validation_and_frontmatter(test_environment):
    """Test note validation and frontmatter processing."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    note_manager = NoteManager()
    await note_manager.initialize(settings)
    
    # Test note with frontmatter
    note_data = {
        "title": "Frontmatter Test",
        "frontmatter": {
            "tags": ["test", "frontmatter"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "draft"
        },
        "content": "# Frontmatter Test\n\nTesting frontmatter processing."
    }
    
    result = await note_manager.create_note(note_data)
    
    # Verify note creation and frontmatter
    assert result.success is True
    note_path = test_environment["vault_path"] / "Frontmatter Test.md"
    content = note_path.read_text()
    
    assert "---" in content  # Frontmatter delimiters
    assert "tags:" in content
    assert "test" in content and "frontmatter" in content
    assert "status: draft" in content

@pytest.mark.asyncio
async def test_note_relationships(test_environment):
    """Test note relationship management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    note_manager = NoteManager()
    await note_manager.initialize(settings)
    
    # Create related notes
    notes = [
        {
            "title": "Parent Note",
            "content": "# Parent Note\n\nThis is a parent note."
        },
        {
            "title": "Child Note",
            "content": "# Child Note\n\nThis references [[Parent Note]]."
        },
        {
            "title": "Sibling Note",
            "content": "# Sibling Note\n\nThis also references [[Parent Note]]."
        }
    ]
    
    # Create all notes
    for note_data in notes:
        result = await note_manager.create_note(note_data)
        assert result.success is True
    
    # Generate backlinks
    backlinks_result = await note_manager.generate_backlinks()
    assert backlinks_result.success is True
    
    # Verify backlinks
    parent_note = test_environment["vault_path"] / "Parent Note.md"
    content = parent_note.read_text()
    
    assert "Backlinks" in content
    assert "Child Note" in content
    assert "Sibling Note" in content 
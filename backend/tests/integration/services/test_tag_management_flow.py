"""Integration tests for tag management flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.tag_management.tag_manager import TagManager
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with tags."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create notes with various tags
    notes = {
        "python_note.md": """---
tags: [programming, python, tutorial]
---
# Python Programming
A note about Python programming.""",
        
        "data_science.md": """---
tags: [data-science, python, machine-learning]
---
# Data Science
Notes about data science.""",
        
        "meeting_notes.md": """---
tags: [meeting, project]
---
# Meeting Notes
Project meeting discussion.""",
        
        "untagged_note.md": """# Untagged Note
This note has no tags."""
    }
    
    for filename, content in notes.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    # Create necessary directories
    tag_db_path = tmp_path / "tag_db"
    tag_db_path.mkdir()
    
    return {
        "vault_path": test_notes,
        "tag_db_path": tag_db_path
    }

@pytest.mark.asyncio
async def test_tag_database_creation(test_environment):
    """Test the creation and initialization of the tag database."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    await tag_manager.initialize(settings)
    
    # Create tag database
    result = await tag_manager.create_tag_database()
    
    # Verify database creation
    assert result.success is True
    assert result.tag_count > 0
    
    # Verify specific tags
    tags = await tag_manager.get_all_tags()
    assert "python" in tags
    assert "data-science" in tags
    assert "programming" in tags

@pytest.mark.asyncio
async def test_semantic_tag_search(test_environment):
    """Test semantic tag searching."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    await tag_manager.initialize(settings)
    
    # Perform semantic tag search
    search_result = await tag_manager.search_tags("machine learning and data analysis")
    
    # Verify search results
    assert search_result.success is True
    assert len(search_result.tags) > 0
    assert "machine-learning" in search_result.tags
    assert "data-science" in search_result.tags

@pytest.mark.asyncio
async def test_automatic_tag_addition(test_environment):
    """Test automatic tag addition to notes."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    note_manager = NoteManager()
    
    await tag_manager.initialize(settings)
    await note_manager.initialize(settings)
    
    # Create a note without tags
    note_data = {
        "title": "Machine Learning Project",
        "content": """# Machine Learning Project
This project involves using Python for deep learning and neural networks.
We'll be using TensorFlow and PyTorch."""
    }
    
    note_result = await note_manager.create_note(note_data)
    assert note_result.success is True
    
    # Auto-tag the note
    tag_result = await tag_manager.auto_tag_note(note_result.note_path)
    
    # Verify auto-tagging
    assert tag_result.success is True
    assert len(tag_result.added_tags) > 0
    assert "machine-learning" in tag_result.added_tags
    assert "python" in tag_result.added_tags
    
    # Verify note content
    note_content = Path(note_result.note_path).read_text()
    assert "tags:" in note_content
    for tag in tag_result.added_tags:
        assert tag in note_content

@pytest.mark.asyncio
async def test_tag_hierarchy_management(test_environment):
    """Test tag hierarchy management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    await tag_manager.initialize(settings)
    
    # Create tag hierarchy
    hierarchy = {
        "programming": ["python", "javascript"],
        "data-science": ["machine-learning", "statistics"],
        "project": ["meeting", "documentation"]
    }
    
    result = await tag_manager.create_tag_hierarchy(hierarchy)
    
    # Verify hierarchy creation
    assert result.success is True
    
    # Test hierarchy queries
    children = await tag_manager.get_child_tags("programming")
    assert "python" in children
    assert "javascript" in children
    
    parent = await tag_manager.get_parent_tag("python")
    assert parent == "programming"

@pytest.mark.asyncio
async def test_tag_statistics_and_analysis(test_environment):
    """Test tag statistics and analysis."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    await tag_manager.initialize(settings)
    
    # Generate tag statistics
    stats_result = await tag_manager.generate_tag_statistics()
    
    # Verify statistics
    assert stats_result.success is True
    assert stats_result.total_tags > 0
    assert stats_result.tag_frequencies["python"] >= 2  # Used in at least 2 notes
    assert stats_result.unused_tags is not None
    
    # Test co-occurrence analysis
    cooccurrence = await tag_manager.analyze_tag_cooccurrence()
    assert ("python", "data-science") in cooccurrence.common_pairs

@pytest.mark.asyncio
async def test_tag_validation_and_normalization(test_environment):
    """Test tag validation and normalization."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        TAG_DB_PATH=str(test_environment["tag_db_path"])
    )
    
    tag_manager = TagManager()
    await tag_manager.initialize(settings)
    
    # Test tag validation
    valid_tags = ["machine-learning", "python3", "data-science"]
    invalid_tags = ["machine learning", "python#", "data/science"]
    
    for tag in valid_tags:
        assert await tag_manager.validate_tag(tag) is True
    
    for tag in invalid_tags:
        assert await tag_manager.validate_tag(tag) is False
    
    # Test tag normalization
    normalized = await tag_manager.normalize_tag("Machine Learning")
    assert normalized == "machine-learning"
    
    normalized = await tag_manager.normalize_tag("Python 3.9")
    assert normalized == "python-3-9" 
"""Integration tests for note reorganization flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.reorganization.reorganizer import NoteReorganizer
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with overlapping content."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create notes with overlapping content
    notes = {
        "project_overview.md": """# Project Overview
This is a project about machine learning.

## Goals
- Implement ML models
- Analyze data
- Deploy models""",
        
        "ml_notes.md": """# Machine Learning Notes
Notes about implementing machine learning models.

## Implementation
- Choose algorithms
- Train models
- Evaluate performance""",
        
        "data_analysis.md": """# Data Analysis
Analysis of project data.

## Steps
- Data cleaning
- Feature engineering
- Model training""",
        
        "large_note.md": """# Complex Topic
This note has become too large and should be split.

## Section 1
Content for section 1...

## Section 2
Content for section 2...

## Section 3
Content for section 3...

## Section 4
Content for section 4..."""
    }
    
    for filename, content in notes.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    return {
        "vault_path": test_notes
    }

@pytest.mark.asyncio
async def test_content_analysis_flow(test_environment):
    """Test the content analysis flow."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    await reorganizer.initialize(settings)
    
    # Analyze note relationships
    analysis_result = await reorganizer.analyze_content()
    
    # Verify analysis results
    assert analysis_result.success is True
    assert analysis_result.relationships is not None
    assert len(analysis_result.relationships) > 0
    
    # Check specific relationships
    relationships = analysis_result.relationships
    assert any(r for r in relationships if "project_overview.md" in r.source and "ml_notes.md" in r.target)
    assert any(r for r in relationships if "data_analysis.md" in r.source and "ml_notes.md" in r.target)

@pytest.mark.asyncio
async def test_note_splitting_flow(test_environment):
    """Test the note splitting process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    await reorganizer.initialize(settings)
    
    # Split large note
    split_result = await reorganizer.split_note("large_note.md")
    
    # Verify split results
    assert split_result.success is True
    assert len(split_result.new_notes) > 1
    
    # Check new notes
    for note_path in split_result.new_notes:
        assert Path(note_path).exists()
        content = Path(note_path).read_text()
        assert "Section" in content
        assert "Content for section" in content

@pytest.mark.asyncio
async def test_note_merging_flow(test_environment):
    """Test the note merging process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    await reorganizer.initialize(settings)
    
    # Merge related notes
    notes_to_merge = ["project_overview.md", "ml_notes.md"]
    merge_result = await reorganizer.merge_notes(notes_to_merge)
    
    # Verify merge results
    assert merge_result.success is True
    assert merge_result.merged_note_path is not None
    
    # Check merged note
    merged_note = Path(merge_result.merged_note_path)
    assert merged_note.exists()
    content = merged_note.read_text()
    assert "Project Overview" in content
    assert "Machine Learning Notes" in content
    assert "Implementation" in content

@pytest.mark.asyncio
async def test_backlink_update_flow(test_environment):
    """Test the backlink update process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    note_manager = NoteManager()
    
    await reorganizer.initialize(settings)
    await note_manager.initialize(settings)
    
    # Create notes with links
    link_notes = {
        "source_note.md": """# Source Note
This links to [[project_overview]] and [[ml_notes]].""",
        "another_note.md": """# Another Note
Reference to [[project_overview#Goals]]."""
    }
    
    for filename, content in link_notes.items():
        note_path = test_environment["vault_path"] / filename
        note_path.write_text(content)
    
    # Merge notes and update backlinks
    notes_to_merge = ["project_overview.md", "ml_notes.md"]
    merge_result = await reorganizer.merge_notes(notes_to_merge)
    update_result = await reorganizer.update_backlinks(merge_result.merged_note_path)
    
    # Verify backlink updates
    assert update_result.success is True
    
    # Check updated notes
    source_note = test_environment["vault_path"] / "source_note.md"
    another_note = test_environment["vault_path"] / "another_note.md"
    
    source_content = source_note.read_text()
    another_content = another_note.read_text()
    
    assert merge_result.merged_note_path.name in source_content
    assert merge_result.merged_note_path.name in another_content

@pytest.mark.asyncio
async def test_structure_update_flow(test_environment):
    """Test the structure update process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    await reorganizer.initialize(settings)
    
    # Update note structure
    structure_result = await reorganizer.update_structure()
    
    # Verify structure updates
    assert structure_result.success is True
    assert structure_result.updated_files is not None
    assert len(structure_result.updated_files) > 0
    
    # Check specific updates
    for file_path in structure_result.updated_files:
        content = Path(file_path).read_text()
        assert "# " in content  # Should have headers
        assert not content.startswith("\n")  # No leading blank lines
        assert "---" in content  # Should have frontmatter

@pytest.mark.asyncio
async def test_conflict_resolution_flow(test_environment):
    """Test the conflict resolution process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"])
    )
    
    reorganizer = NoteReorganizer()
    await reorganizer.initialize(settings)
    
    # Create conflicting changes
    notes_to_merge = ["project_overview.md", "ml_notes.md"]
    
    # Modify one of the notes before merging
    ml_notes_path = test_environment["vault_path"] / "ml_notes.md"
    original_content = ml_notes_path.read_text()
    ml_notes_path.write_text(original_content + "\n\n## New Section\nNew content...")
    
    # Attempt merge with conflict resolution
    merge_result = await reorganizer.merge_notes(notes_to_merge, resolve_conflicts=True)
    
    # Verify conflict resolution
    assert merge_result.success is True
    assert merge_result.had_conflicts is True
    assert merge_result.resolved_conflicts is not None
    
    # Check merged content
    merged_content = Path(merge_result.merged_note_path).read_text()
    assert "New Section" in merged_content
    assert "New content" in merged_content 
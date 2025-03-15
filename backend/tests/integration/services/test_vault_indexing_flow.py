"""Integration tests for vault indexing flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.indexing.indexer import VaultIndexer
from src.services.search.search_service import SearchService
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_vault(tmp_path) -> Path:
    """Create a test vault with various file types and structures."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create directory structure
    (vault_path / "daily").mkdir()
    (vault_path / "projects").mkdir()
    (vault_path / "references").mkdir()
    (vault_path / "attachments").mkdir()
    
    # Create various types of files
    files = {
        "daily/2024-01-15.md": """# Daily Note
- Meeting with team
- Started new project
- TODO: Follow up with client""",
        
        "projects/project_alpha.md": """# Project Alpha
Status: In Progress
Start Date: 2024-01-10

## Overview
This is a major project with multiple components.

## Tasks
1. Design phase
2. Implementation
3. Testing""",
        
        "references/technical_spec.md": """# Technical Specification
## Architecture
- Component A
- Component B
- Component C

## Implementation Details
Details about the implementation...""",
        
        "attachments/diagram.svg": "<svg>Test SVG content</svg>",
        
        "README.md": """# Vault README
This is the main documentation for the vault."""
    }
    
    for filepath, content in files.items():
        file_path = vault_path / filepath
        file_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_vault):
    """Set up test environment."""
    # Create necessary directories
    index_path = tmp_path / "index"
    index_path.mkdir()
    cache_path = tmp_path / "cache"
    cache_path.mkdir()
    
    return {
        "vault_path": test_vault,
        "index_path": index_path,
        "cache_path": cache_path
    }

@pytest.mark.asyncio
async def test_initial_indexing(test_environment):
    """Test initial vault indexing process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"]),
        CACHE_PATH=str(test_environment["cache_path"])
    )
    
    indexer = VaultIndexer()
    await indexer.initialize(settings)
    
    # Perform initial indexing
    result = await indexer.index_vault()
    
    # Verify indexing results
    assert result.success is True
    assert result.indexed_files > 0
    assert result.index_size > 0
    
    # Check specific file indexing
    assert "daily/2024-01-15.md" in result.indexed_files_list
    assert "projects/project_alpha.md" in result.indexed_files_list

@pytest.mark.asyncio
async def test_incremental_indexing(test_environment):
    """Test incremental indexing of new and modified files."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    indexer = VaultIndexer()
    await indexer.initialize(settings)
    
    # Perform initial indexing
    await indexer.index_vault()
    
    # Add new file
    new_file = test_environment["vault_path"] / "projects/new_project.md"
    new_file.write_text("# New Project\nThis is a new project file.")
    
    # Modify existing file
    existing_file = test_environment["vault_path"] / "daily/2024-01-15.md"
    original_content = existing_file.read_text()
    existing_file.write_text(original_content + "\n- New task added")
    
    # Perform incremental indexing
    result = await indexer.incremental_index()
    
    # Verify incremental indexing
    assert result.success is True
    assert "projects/new_project.md" in result.updated_files
    assert "daily/2024-01-15.md" in result.updated_files

@pytest.mark.asyncio
async def test_metadata_extraction(test_environment):
    """Test extraction and indexing of file metadata."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    indexer = VaultIndexer()
    await indexer.initialize(settings)
    
    # Extract metadata
    result = await indexer.extract_metadata()
    
    # Verify metadata extraction
    assert result.success is True
    assert len(result.metadata) > 0
    
    # Check specific metadata
    project_metadata = result.metadata["projects/project_alpha.md"]
    assert project_metadata.title == "Project Alpha"
    assert project_metadata.status == "In Progress"
    assert "2024-01-10" in project_metadata.dates

@pytest.mark.asyncio
async def test_search_integration(test_environment):
    """Test integration with search functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    indexer = VaultIndexer()
    search_service = SearchService()
    
    await indexer.initialize(settings)
    await search_service.initialize(settings)
    
    # Index vault and perform search
    await indexer.index_vault()
    search_result = await search_service.search("project implementation")
    
    # Verify search results
    assert search_result.success is True
    assert len(search_result.matches) > 0
    assert any("project_alpha.md" in match.file for match in search_result.matches)

@pytest.mark.asyncio
async def test_file_type_handling(test_environment):
    """Test handling of different file types."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    indexer = VaultIndexer()
    await indexer.initialize(settings)
    
    # Index different file types
    result = await indexer.index_by_type()
    
    # Verify file type handling
    assert result.success is True
    assert len(result.markdown_files) > 0
    assert len(result.binary_files) > 0
    assert "diagram.svg" in result.binary_files
    assert "README.md" in result.markdown_files

@pytest.mark.asyncio
async def test_index_maintenance(test_environment):
    """Test index maintenance and optimization."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        INDEX_PATH=str(test_environment["index_path"])
    )
    
    indexer = VaultIndexer()
    await indexer.initialize(settings)
    
    # Perform initial indexing
    await indexer.index_vault()
    
    # Run maintenance tasks
    result = await indexer.maintain_index()
    
    # Verify maintenance results
    assert result.success is True
    assert result.optimized_size < result.original_size
    assert result.integrity_check_passed is True
    
    # Verify index statistics
    stats = await indexer.get_index_statistics()
    assert stats.total_documents > 0
    assert stats.index_size > 0
    assert stats.last_optimization is not None 
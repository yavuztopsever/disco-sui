"""Integration tests for search and discovery flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.search.search_service import SearchService
from src.services.indexing.indexer import VaultIndexer
from src.services.discovery.discovery_service import DiscoveryService
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with varied content for search testing."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create notes with diverse content and metadata
    notes = {
        "programming/python.md": """---
tags: [programming, python, tutorial]
created: 2024-01-15
---
# Python Programming Guide
Python is a versatile programming language.

## Key Features
- Easy to learn
- Rich ecosystem
- Great for data science

## Code Examples
```python
def hello_world():
    print("Hello, World!")
```""",
        
        "data_science/machine_learning.md": """---
tags: [data-science, machine-learning, python]
created: 2024-01-16
---
# Machine Learning Basics
Introduction to machine learning concepts.

## Topics
- Supervised Learning
- Neural Networks
- Deep Learning

## Tools
- TensorFlow
- PyTorch
- scikit-learn""",
        
        "projects/project_notes.md": """---
tags: [project, planning]
status: in-progress
priority: high
---
# Project Planning
Project implementation details and timeline.

## Tasks
1. Setup development environment
2. Implement core features
3. Write documentation

## Dependencies
- Python 3.8+
- TensorFlow
- Docker""",
        
        "daily/meeting_notes.md": """---
date: 2024-01-17
participants: [alice, bob, charlie]
---
# Team Meeting Notes
Discussion about project progress.

## Action Items
- Review ML models
- Update documentation
- Schedule follow-up

## Decisions
- Use TensorFlow for ML
- Deploy using Docker"""
    }
    
    # Create directory structure and notes
    for filepath, content in notes.items():
        file_path = vault_path / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    # Create necessary directories
    search_index_path = tmp_path / "search_index"
    search_index_path.mkdir()
    discovery_cache_path = tmp_path / "discovery_cache"
    discovery_cache_path.mkdir()
    
    return {
        "vault_path": test_notes,
        "search_index_path": search_index_path,
        "discovery_cache_path": discovery_cache_path
    }

@pytest.mark.asyncio
async def test_full_text_search(test_environment):
    """Test full-text search capabilities."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    indexer = VaultIndexer()
    
    await search_service.initialize(settings)
    await indexer.initialize(settings)
    
    # Index content
    await indexer.index_vault()
    
    # Perform various searches
    results = await search_service.search("python programming")
    
    # Verify search results
    assert results.success is True
    assert len(results.matches) > 0
    assert any("python.md" in match.file for match in results.matches)
    assert results.matches[0].relevance > 0.5

@pytest.mark.asyncio
async def test_tag_based_search(test_environment):
    """Test tag-based search functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    await search_service.initialize(settings)
    
    # Search by tags
    results = await search_service.search_by_tags(["python", "machine-learning"])
    
    # Verify results
    assert results.success is True
    assert len(results.matches) > 0
    assert any("machine_learning.md" in match.file for match in results.matches)
    assert all("python" in match.tags for match in results.matches)

@pytest.mark.asyncio
async def test_metadata_search(test_environment):
    """Test metadata-based search capabilities."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    await search_service.initialize(settings)
    
    # Search by metadata
    results = await search_service.search_by_metadata({
        "status": "in-progress",
        "priority": "high"
    })
    
    # Verify results
    assert results.success is True
    assert len(results.matches) > 0
    assert any("project_notes.md" in match.file for match in results.matches)

@pytest.mark.asyncio
async def test_content_discovery(test_environment):
    """Test content discovery and recommendations."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        DISCOVERY_CACHE_PATH=str(test_environment["discovery_cache_path"])
    )
    
    discovery_service = DiscoveryService()
    await discovery_service.initialize(settings)
    
    # Get content recommendations
    recommendations = await discovery_service.get_recommendations(
        source_file="programming/python.md"
    )
    
    # Verify recommendations
    assert recommendations.success is True
    assert len(recommendations.related_files) > 0
    assert any("machine_learning.md" in file for file in recommendations.related_files)

@pytest.mark.asyncio
async def test_search_filters(test_environment):
    """Test search filter functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    await search_service.initialize(settings)
    
    # Search with filters
    filters = {
        "created_after": "2024-01-16",
        "tags": ["project"],
        "path_contains": "projects"
    }
    
    results = await search_service.filtered_search("implementation", filters)
    
    # Verify filtered results
    assert results.success is True
    assert all(result.created >= "2024-01-16" for result in results.matches)
    assert all("project" in result.tags for result in results.matches)

@pytest.mark.asyncio
async def test_search_ranking(test_environment):
    """Test search result ranking and relevance scoring."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    await search_service.initialize(settings)
    
    # Perform search with ranking
    results = await search_service.ranked_search("machine learning python")
    
    # Verify ranking
    assert results.success is True
    assert len(results.matches) > 1
    assert results.matches[0].relevance >= results.matches[1].relevance
    assert "machine_learning.md" in results.matches[0].file

@pytest.mark.asyncio
async def test_discovery_patterns(test_environment):
    """Test pattern discovery in content."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        DISCOVERY_CACHE_PATH=str(test_environment["discovery_cache_path"])
    )
    
    discovery_service = DiscoveryService()
    await discovery_service.initialize(settings)
    
    # Analyze content patterns
    patterns = await discovery_service.analyze_patterns()
    
    # Verify pattern analysis
    assert patterns.success is True
    assert len(patterns.topic_clusters) > 0
    assert len(patterns.common_references) > 0
    assert "python" in patterns.frequent_terms

@pytest.mark.asyncio
async def test_search_suggestions(test_environment):
    """Test search suggestions and autocomplete."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEARCH_INDEX_PATH=str(test_environment["search_index_path"])
    )
    
    search_service = SearchService()
    await search_service.initialize(settings)
    
    # Get search suggestions
    suggestions = await search_service.get_suggestions("py")
    
    # Verify suggestions
    assert suggestions.success is True
    assert len(suggestions.terms) > 0
    assert "python" in suggestions.terms
    assert all(term.startswith("py") for term in suggestions.terms) 
"""Integration tests for semantic analysis flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.semantic.semantic_analyzer import SemanticAnalyzer
from src.services.note_management.note_manager import NoteManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with varied semantic content."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create notes with semantically related content
    notes = {
        "machine_learning.md": """# Machine Learning
Machine learning is a subset of artificial intelligence that focuses on data and algorithms.

## Key Concepts
- Neural Networks
- Deep Learning
- Supervised Learning
- Unsupervised Learning""",
        
        "deep_learning.md": """# Deep Learning
Deep learning is a type of machine learning using neural networks with multiple layers.

## Applications
- Image Recognition
- Natural Language Processing
- Speech Recognition""",
        
        "data_science.md": """# Data Science
Data science combines statistics, programming, and domain knowledge.

## Tools
- Python
- TensorFlow
- PyTorch
- Scikit-learn""",
        
        "project_notes.md": """# Project Meeting Notes
Discussed implementing a neural network for our image classification project.
We'll be using TensorFlow and need to collect more training data."""
    }
    
    for filename, content in notes.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    # Create necessary directories
    semantic_db_path = tmp_path / "semantic_db"
    semantic_db_path.mkdir()
    
    return {
        "vault_path": test_notes,
        "semantic_db_path": semantic_db_path
    }

@pytest.mark.asyncio
async def test_semantic_embedding_generation(test_environment):
    """Test generation of semantic embeddings."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Generate embeddings for all notes
    result = await analyzer.generate_embeddings()
    
    # Verify embedding generation
    assert result.success is True
    assert result.embedding_count > 0
    assert all(result.embeddings[note] is not None for note in result.embeddings)

@pytest.mark.asyncio
async def test_semantic_similarity_analysis(test_environment):
    """Test semantic similarity analysis between notes."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Analyze semantic similarities
    result = await analyzer.analyze_similarities()
    
    # Verify similarity analysis
    assert result.success is True
    assert len(result.similarity_scores) > 0
    
    # Check specific similarities
    assert result.similarity_scores[("machine_learning.md", "deep_learning.md")] > 0.7  # High similarity
    assert result.similarity_scores[("machine_learning.md", "project_notes.md")] > 0.5  # Moderate similarity

@pytest.mark.asyncio
async def test_topic_extraction(test_environment):
    """Test automatic topic extraction from notes."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Extract topics
    result = await analyzer.extract_topics()
    
    # Verify topic extraction
    assert result.success is True
    assert len(result.topics) > 0
    
    # Check specific topics
    topics = result.topics
    assert any("machine learning" in topic.lower() for topic in topics)
    assert any("neural network" in topic.lower() for topic in topics)
    assert any("data science" in topic.lower() for topic in topics)

@pytest.mark.asyncio
async def test_semantic_clustering(test_environment):
    """Test semantic clustering of notes."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Perform semantic clustering
    result = await analyzer.cluster_notes()
    
    # Verify clustering results
    assert result.success is True
    assert len(result.clusters) > 0
    
    # Check cluster contents
    ml_cluster = next(cluster for cluster in result.clusters 
                     if "machine_learning.md" in cluster.notes)
    assert "deep_learning.md" in ml_cluster.notes  # Should be in same cluster

@pytest.mark.asyncio
async def test_semantic_search(test_environment):
    """Test semantic search functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Perform semantic search
    query = "neural networks for image classification"
    result = await analyzer.semantic_search(query)
    
    # Verify search results
    assert result.success is True
    assert len(result.matches) > 0
    
    # Check relevance of results
    assert "deep_learning.md" in [match.note for match in result.matches[:2]]
    assert "project_notes.md" in [match.note for match in result.matches[:3]]

@pytest.mark.asyncio
async def test_concept_graph_generation(test_environment):
    """Test generation of concept relationship graphs."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        SEMANTIC_DB_PATH=str(test_environment["semantic_db_path"])
    )
    
    analyzer = SemanticAnalyzer()
    await analyzer.initialize(settings)
    
    # Generate concept graph
    result = await analyzer.generate_concept_graph()
    
    # Verify graph generation
    assert result.success is True
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    
    # Check specific concepts and relationships
    assert any(node.label == "machine learning" for node in result.nodes)
    assert any(node.label == "neural networks" for node in result.nodes)
    assert any(edge.source == "deep learning" and edge.target == "neural networks" 
              for edge in result.edges) 
"""Integration tests for RAG query flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime

from src.core.config import Settings
from src.services.rag.rag_service import RAGService
from src.services.indexing.indexer import VaultIndexer
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_notes(tmp_path) -> Path:
    """Create test notes with varied content."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create sample notes with different topics
    notes = {
        "python.md": """# Python Programming
Python is a high-level programming language known for its simplicity and readability.

## Key Features
- Easy to learn
- Large standard library
- Dynamic typing
- Object-oriented

## Common Uses
- Web development
- Data science
- Machine learning
- Automation""",
        
        "javascript.md": """# JavaScript
JavaScript is a programming language commonly used for web development.

## Features
- Client-side scripting
- Event-driven programming
- Asynchronous operations
- DOM manipulation""",
        
        "data_science.md": """# Data Science
Data science combines programming, statistics, and domain knowledge.

## Tools
- Python libraries (pandas, numpy)
- Machine learning frameworks
- Statistical analysis
- Data visualization

## Applications
- Predictive analytics
- Pattern recognition
- Business intelligence"""
    }
    
    for filename, content in notes.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_notes):
    """Set up test environment."""
    # Create necessary directories
    vector_db_path = tmp_path / "vector_db"
    vector_db_path.mkdir()
    
    return {
        "vault_path": test_notes,
        "vector_db_path": vector_db_path
    }

@pytest.mark.asyncio
async def test_query_processing_flow(test_environment):
    """Test the query processing and enhancement flow."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    rag_service = RAGService()
    await rag_service.initialize(settings)
    
    # Test query processing
    query = "What are the main uses of Python?"
    processed_query = await rag_service.process_query(query)
    
    # Verify query processing
    assert processed_query is not None
    assert len(processed_query) > len(query)  # Enhanced query should be more detailed
    assert "Python" in processed_query
    assert "uses" in processed_query.lower()

@pytest.mark.asyncio
async def test_vector_search_flow(test_environment):
    """Test the vector search process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    rag_service = RAGService()
    indexer = VaultIndexer()
    
    await rag_service.initialize(settings)
    await indexer.initialize(settings)
    
    # Index the test vault
    await indexer.index_vault()
    
    # Perform vector search
    query = "What is Python used for?"
    results = await rag_service.vector_search(query)
    
    # Verify search results
    assert results is not None
    assert len(results) > 0
    assert any("Python" in chunk.content for chunk in results)
    assert any("web development" in chunk.content.lower() for chunk in results)
    assert any("data science" in chunk.content.lower() for chunk in results)

@pytest.mark.asyncio
async def test_context_retrieval_flow(test_environment):
    """Test the context retrieval and ranking process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    rag_service = RAGService()
    indexer = VaultIndexer()
    
    await rag_service.initialize(settings)
    await indexer.initialize(settings)
    
    # Index the vault and retrieve context
    await indexer.index_vault()
    query = "Explain data science tools and applications"
    context = await rag_service.get_context(query)
    
    # Verify context
    assert context is not None
    assert len(context) > 0
    assert any("data science" in chunk.lower() for chunk in context)
    assert any("python" in chunk.lower() for chunk in context)
    assert any("machine learning" in chunk.lower() for chunk in context)

@pytest.mark.asyncio
async def test_response_generation_flow(test_environment):
    """Test the response generation process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    rag_service = RAGService()
    indexer = VaultIndexer()
    
    await rag_service.initialize(settings)
    await indexer.initialize(settings)
    
    # Index vault and generate response
    await indexer.index_vault()
    query = "Compare Python and JavaScript"
    response = await rag_service.generate_response(query)
    
    # Verify response
    assert response is not None
    assert response.content is not None
    assert "Python" in response.content
    assert "JavaScript" in response.content
    assert len(response.citations) > 0
    assert any("python.md" in citation for citation in response.citations)
    assert any("javascript.md" in citation for citation in response.citations)

@pytest.mark.asyncio
async def test_citation_generation_flow(test_environment):
    """Test the citation generation process."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"])
    )
    
    rag_service = RAGService()
    indexer = VaultIndexer()
    
    await rag_service.initialize(settings)
    await indexer.initialize(settings)
    
    # Index vault and generate response with citations
    await indexer.index_vault()
    query = "What tools are used in data science?"
    response = await rag_service.generate_response(query)
    
    # Verify citations
    assert response.citations is not None
    assert len(response.citations) > 0
    assert any("data_science.md" in citation for citation in response.citations)
    
    # Verify citation format
    for citation in response.citations:
        assert "#" in citation  # Should include section references
        assert "|" in citation  # Should include relevance scores 
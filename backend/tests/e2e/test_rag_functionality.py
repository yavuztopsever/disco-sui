"""End-to-end tests for RAG (Retrieval Augmented Generation) functionality."""

import pytest
import os
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.NoteManagementAgent import NoteManagementAgent
from src.services.indexing.indexer import Indexer
from src.services.indexing.rag import RAG
from src.core.exceptions import (
    NoteManagementError,
    IndexingError,
    RAGError
)

@pytest.fixture
async def test_vault(tmp_path) -> Path:
    """Create a temporary test vault with test notes."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    
    # Create basic vault structure
    (vault_path / ".obsidian").mkdir()
    (vault_path / ".obsidian" / "plugins").mkdir()
    
    # Create test notes
    notes = {
        "Python Programming.md": """# Python Programming
Python is a versatile programming language known for its simplicity and readability.

## Key Features
- Easy to learn
- Large standard library
- Extensive third-party packages
- Cross-platform compatibility

## Common Use Cases
- Web development with Django and Flask
- Data analysis with pandas and numpy
- Machine learning with scikit-learn
- Automation and scripting""",
        
        "Machine Learning.md": """# Machine Learning
Machine learning is a subset of artificial intelligence focused on data-driven algorithms.

## Types of Learning
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning

## Popular Libraries
- scikit-learn
- TensorFlow
- PyTorch
- Keras""",
        
        "Web Development.md": """# Web Development
Web development involves creating websites and web applications.

## Frontend Technologies
- HTML
- CSS
- JavaScript
- React

## Backend Technologies
- Python (Django, Flask)
- Node.js
- Ruby on Rails
- PHP""",
        
        "Data Analysis.md": """# Data Analysis
Data analysis is the process of inspecting and modeling data.

## Tools and Libraries
- Python pandas
- R
- SQL
- Excel

## Common Techniques
- Statistical analysis
- Data visualization
- Data cleaning
- Feature engineering"""
    }
    
    for filename, content in notes.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
async def note_management_agent(test_vault) -> NoteManagementAgent:
    """Create a NoteManagementAgent instance."""
    agent = NoteManagementAgent(str(test_vault))
    return agent

@pytest.fixture
async def indexer(test_vault) -> Indexer:
    """Create an Indexer instance."""
    indexer = Indexer()
    await indexer.initialize(test_vault)
    return indexer

@pytest.fixture
async def rag(test_vault, indexer) -> RAG:
    """Create a RAG instance."""
    rag = RAG()
    await rag.initialize(test_vault, indexer)
    return rag

@pytest.mark.asyncio
class TestRAGFunctionality:
    """Test suite for RAG functionality."""
    
    async def test_indexing(self, indexer, test_vault):
        """Test note indexing functionality."""
        # Index all notes
        index_result = await indexer.index_vault()
        assert index_result["success"] is True
        assert index_result["indexed_count"] == 4
        
        # Verify index status
        status = await indexer.get_index_status()
        assert status["total_notes"] == 4
        assert status["last_indexed"] is not None
        
        # Test incremental indexing
        new_note = test_vault / "New Note.md"
        new_note.write_text("# New Note\nThis is a test note.")
        
        update_result = await indexer.update_index()
        assert update_result["success"] is True
        assert update_result["updated_count"] == 1
    
    async def test_chunking(self, indexer):
        """Test document chunking functionality."""
        # Test different chunking strategies
        chunk_configs = [
            {"strategy": "sentence", "max_length": 100},
            {"strategy": "paragraph", "max_length": 200},
            {"strategy": "fixed", "chunk_size": 150, "overlap": 50}
        ]
        
        for config in chunk_configs:
            chunks = await indexer.chunk_document(
                "Python is a versatile language. It is easy to learn. " * 10,
                config
            )
            assert len(chunks) > 0
            if config["strategy"] != "fixed":
                assert all(len(chunk) <= config["max_length"] for chunk in chunks)
            else:
                assert all(len(chunk) <= config["chunk_size"] for chunk in chunks)
    
    async def test_embeddings(self, indexer):
        """Test embedding generation functionality."""
        # Test embedding generation
        text = "Python is a versatile programming language."
        embedding = await indexer.generate_embedding(text)
        assert len(embedding) > 0
        
        # Test batch embedding
        texts = [
            "Python is versatile",
            "Machine learning is powerful",
            "Data analysis is important"
        ]
        embeddings = await indexer.generate_embeddings(texts)
        assert len(embeddings) == 3
        assert all(len(emb) > 0 for emb in embeddings)
    
    async def test_similarity_search(self, rag):
        """Test similarity search functionality."""
        # Test basic similarity search
        results = await rag.similarity_search(
            "What are the main features of Python?",
            max_results=2
        )
        assert len(results) == 2
        assert any("Python Programming" in result["source"] for result in results)
        
        # Test search with filters
        filtered_results = await rag.similarity_search(
            "What are machine learning libraries?",
            max_results=2,
            filters={"category": "Machine Learning"}
        )
        assert len(filtered_results) == 2
        assert all("Machine Learning" in result["source"] for result in filtered_results)
    
    async def test_query_processing(self, rag):
        """Test query processing functionality."""
        # Test query expansion
        expanded_query = await rag.expand_query(
            "Python web frameworks"
        )
        assert len(expanded_query) > len("Python web frameworks")
        assert "Django" in expanded_query or "Flask" in expanded_query
        
        # Test query classification
        query_type = await rag.classify_query(
            "What are the best Python libraries for data analysis?"
        )
        assert query_type in ["informational", "comparison", "recommendation"]
    
    async def test_context_retrieval(self, rag):
        """Test context retrieval functionality."""
        # Test context retrieval
        context = await rag.get_context(
            "How can I use Python for data analysis?"
        )
        assert len(context) > 0
        assert any("pandas" in c["text"] for c in context)
        assert any("data analysis" in c["text"].lower() for c in context)
        
        # Test context ranking
        ranked_context = await rag.rank_context(
            "What are popular machine learning libraries?",
            context
        )
        assert len(ranked_context) > 0
        assert ranked_context[0]["relevance_score"] >= ranked_context[-1]["relevance_score"]
    
    async def test_response_generation(self, rag):
        """Test response generation functionality."""
        # Test basic response generation
        response = await rag.generate_response(
            "What are the main uses of Python?"
        )
        assert response["success"] is True
        assert "web development" in response["text"].lower()
        assert "data analysis" in response["text"].lower()
        
        # Test response with citations
        response_with_citations = await rag.generate_response(
            "What are popular machine learning libraries?",
            include_citations=True
        )
        assert response_with_citations["success"] is True
        assert "citations" in response_with_citations
        assert len(response_with_citations["citations"]) > 0
    
    async def test_integration_with_agent(self, note_management_agent):
        """Test RAG integration with NoteManagementAgent."""
        # Test question answering
        result = await note_management_agent.process_message(
            "What are the main features of Python and its common use cases?"
        )
        assert result["success"] is True
        assert "versatile" in result["response"].lower()
        assert "web development" in result["response"].lower()
        
        # Test follow-up questions
        follow_up = await note_management_agent.process_message(
            "Tell me more about its use in data analysis"
        )
        assert follow_up["success"] is True
        assert "pandas" in follow_up["response"].lower()
    
    async def test_error_handling(self, rag):
        """Test RAG error handling."""
        # Test invalid query
        with pytest.raises(RAGError):
            await rag.generate_response("")
        
        # Test missing context
        with patch.object(rag, "get_context", return_value=[]):
            result = await rag.generate_response(
                "What is the meaning of life?"
            )
            assert result["success"] is False
            assert "insufficient context" in result["error"].lower()
    
    async def test_performance(self, rag):
        """Test RAG performance metrics."""
        # Test response time
        start_time = datetime.now()
        await rag.generate_response(
            "What are the main features of Python?"
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        assert response_time < 5  # Response should be generated within 5 seconds
        
        # Test concurrent requests
        queries = [
            "What is Python?",
            "What is machine learning?",
            "What is web development?",
            "What is data analysis?"
        ]
        
        start_time = datetime.now()
        results = await asyncio.gather(*[
            rag.generate_response(query)
            for query in queries
        ])
        end_time = datetime.now()
        
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 20  # All responses should be generated within 20 seconds
        assert all(result["success"] for result in results)
    
    async def test_caching(self, rag):
        """Test RAG caching functionality."""
        # Make initial request
        query = "What are the main features of Python?"
        first_response = await rag.generate_response(query)
        
        # Make same request again (should use cache)
        start_time = datetime.now()
        cached_response = await rag.generate_response(query)
        end_time = datetime.now()
        
        cache_response_time = (end_time - start_time).total_seconds()
        assert cache_response_time < 1  # Cached response should be very fast
        assert cached_response["text"] == first_response["text"] 
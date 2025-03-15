import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.analysis.semantic.vault_indexer import VaultIndexer

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def mock_embeddings():
    return MagicMock()

@pytest.fixture
def mock_vector_db():
    return MagicMock()

@pytest.fixture
def vault_indexer(mock_context, mock_storage, mock_embeddings, mock_vector_db):
    return VaultIndexer(
        context=mock_context,
        storage=mock_storage,
        embeddings=mock_embeddings,
        vector_db=mock_vector_db
    )

def test_vault_indexer_initialization(vault_indexer):
    """Test vault indexer initialization."""
    assert vault_indexer is not None
    assert vault_indexer.storage is not None
    assert vault_indexer.embeddings is not None
    assert vault_indexer.vector_db is not None

def test_index_vault(vault_indexer, mock_storage, mock_vector_db):
    """Test indexing entire vault."""
    mock_storage.list_notes.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md"]
    }
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content"
    }
    mock_vector_db.add_documents.return_value = {
        "success": True,
        "added": 2
    }
    
    result = vault_indexer.index_vault()
    assert result["success"] is True
    assert result["indexed_count"] == 2

def test_index_note(vault_indexer, mock_storage, mock_embeddings):
    """Test indexing single note."""
    note_path = "test/note.md"
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content",
        "metadata": {"title": "Test Note"}
    }
    mock_embeddings.embed_text.return_value = {
        "success": True,
        "embedding": [0.1, 0.2, 0.3]
    }
    
    result = vault_indexer.index_note(note_path)
    assert result["success"] is True
    assert "embedding" in result

def test_update_index(vault_indexer, mock_vector_db):
    """Test updating index."""
    note_path = "test/note.md"
    embedding = [0.1, 0.2, 0.3]
    mock_vector_db.update_document.return_value = {
        "success": True,
        "updated": True
    }
    
    result = vault_indexer.update_index(note_path, embedding)
    assert result["success"] is True
    assert result["updated"] is True

def test_remove_from_index(vault_indexer, mock_vector_db):
    """Test removing note from index."""
    note_path = "test/note.md"
    mock_vector_db.remove_document.return_value = {
        "success": True,
        "removed": True
    }
    
    result = vault_indexer.remove_from_index(note_path)
    assert result["success"] is True
    assert result["removed"] is True

def test_search_similar(vault_indexer, mock_embeddings, mock_vector_db):
    """Test searching similar notes."""
    query = "test query"
    mock_embeddings.embed_text.return_value = {
        "success": True,
        "embedding": [0.1, 0.2, 0.3]
    }
    mock_vector_db.search_similar.return_value = {
        "success": True,
        "results": [
            {"id": "note1.md", "score": 0.9},
            {"id": "note2.md", "score": 0.8}
        ]
    }
    
    result = vault_indexer.search_similar(query)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == 2

def test_get_note_embedding(vault_indexer, mock_vector_db):
    """Test getting note embedding."""
    note_path = "test/note.md"
    mock_vector_db.get_embedding.return_value = {
        "success": True,
        "embedding": [0.1, 0.2, 0.3]
    }
    
    result = vault_indexer.get_note_embedding(note_path)
    assert result["success"] is True
    assert "embedding" in result

def test_batch_index(vault_indexer, mock_storage, mock_vector_db):
    """Test batch indexing."""
    note_paths = ["note1.md", "note2.md"]
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content"
    }
    mock_vector_db.add_documents.return_value = {
        "success": True,
        "added": len(note_paths)
    }
    
    result = vault_indexer.batch_index(note_paths)
    assert result["success"] is True
    assert result["indexed_count"] == len(note_paths)

def test_check_index_status(vault_indexer, mock_vector_db):
    """Test checking index status."""
    mock_vector_db.get_stats.return_value = {
        "success": True,
        "stats": {
            "total_documents": 100,
            "indexed_documents": 90
        }
    }
    
    result = vault_indexer.check_index_status()
    assert result["success"] is True
    assert "stats" in result
    assert result["stats"]["total_documents"] == 100

def test_reindex_vault(vault_indexer, mock_vector_db):
    """Test reindexing vault."""
    mock_vector_db.clear_index.return_value = {"success": True}
    mock_vector_db.add_documents.return_value = {
        "success": True,
        "added": 2
    }
    
    result = vault_indexer.reindex_vault()
    assert result["success"] is True
    assert "reindexed_count" in result

def test_error_handling(vault_indexer, mock_storage):
    """Test error handling."""
    mock_storage.list_notes.side_effect = Exception("Test error")
    
    result = vault_indexer.index_vault()
    assert result["success"] is False
    assert "error" in result

def test_validate_embedding(vault_indexer):
    """Test embedding validation."""
    valid_embedding = [0.1, 0.2, 0.3]
    invalid_embedding = "not an embedding"
    
    result = vault_indexer.validate_embedding(valid_embedding)
    assert result["success"] is True
    assert result["valid"] is True
    
    result = vault_indexer.validate_embedding(invalid_embedding)
    assert result["success"] is True
    assert result["valid"] is False 
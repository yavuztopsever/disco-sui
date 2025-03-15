import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.analysis.semantic_analyzer import SemanticAnalyzer

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def mock_model():
    return MagicMock()

@pytest.fixture
def semantic_analyzer(mock_context, mock_storage, mock_model):
    analyzer = SemanticAnalyzer(context=mock_context)
    analyzer._storage = mock_storage
    analyzer._model = mock_model
    return analyzer

def test_analyzer_initialization(semantic_analyzer):
    """Test semantic analyzer initialization."""
    assert semantic_analyzer is not None
    assert semantic_analyzer.context is not None
    assert semantic_analyzer._storage is not None
    assert semantic_analyzer._model is not None

def test_analyze_content(semantic_analyzer, mock_model):
    """Test analyzing content."""
    content = "Test content for semantic analysis"
    mock_model.analyze.return_value = {
        "success": True,
        "analysis": {
            "topics": ["topic1", "topic2"],
            "sentiment": "positive",
            "key_phrases": ["phrase1", "phrase2"]
        }
    }
    
    result = semantic_analyzer.analyze_content(content)
    assert result["success"] is True
    assert "analysis" in result
    assert "topics" in result["analysis"]
    mock_model.analyze.assert_called_once_with(content)

def test_analyze_note(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing a note."""
    note_path = "notes/test.md"
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content"
    }
    mock_model.analyze.return_value = {
        "success": True,
        "analysis": {
            "topics": ["topic1"],
            "references": ["ref1"],
            "complexity": "medium"
        }
    }
    
    result = semantic_analyzer.analyze_note(note_path)
    assert result["success"] is True
    assert "analysis" in result
    assert "topics" in result["analysis"]
    mock_storage.read_note.assert_called_once_with(note_path)
    mock_model.analyze.assert_called_once()

def test_analyze_relationships(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing relationships between notes."""
    notes = ["note1.md", "note2.md"]
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content"
    }
    mock_model.analyze_relationships.return_value = {
        "success": True,
        "relationships": {
            "note1.md": ["note2.md"],
            "note2.md": ["note1.md"]
        }
    }
    
    result = semantic_analyzer.analyze_relationships(notes)
    assert result["success"] is True
    assert "relationships" in result
    assert len(result["relationships"]) == len(notes)
    assert mock_storage.read_note.call_count == len(notes)

def test_analyze_similarity(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing similarity between notes."""
    note1 = "note1.md"
    note2 = "note2.md"
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "Note content"
    }
    mock_model.calculate_similarity.return_value = {
        "success": True,
        "similarity": 0.85,
        "common_topics": ["topic1"]
    }
    
    result = semantic_analyzer.analyze_similarity(note1, note2)
    assert result["success"] is True
    assert "similarity" in result
    assert "common_topics" in result
    assert mock_storage.read_note.call_count == 2

def test_analyze_trends(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing trends."""
    mock_storage.list_notes.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md"]
    }
    mock_model.analyze_trends.return_value = {
        "success": True,
        "trends": {
            "topics": ["trending1", "trending2"],
            "time_periods": ["2024-03", "2024-02"]
        }
    }
    
    result = semantic_analyzer.analyze_trends()
    assert result["success"] is True
    assert "trends" in result
    assert "topics" in result["trends"]
    mock_storage.list_notes.assert_called_once()

def test_generate_summary(semantic_analyzer, mock_model):
    """Test generating summary."""
    content = "Long content to summarize"
    mock_model.generate_summary.return_value = {
        "success": True,
        "summary": "Short summary",
        "key_points": ["point1", "point2"]
    }
    
    result = semantic_analyzer.generate_summary(content)
    assert result["success"] is True
    assert "summary" in result
    assert "key_points" in result
    mock_model.generate_summary.assert_called_once_with(content)

def test_analyze_tags(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing tags."""
    mock_storage.list_tags.return_value = {
        "success": True,
        "tags": ["tag1", "tag2", "tag3"]
    }
    mock_model.analyze_tags.return_value = {
        "success": True,
        "tag_analysis": {
            "most_used": ["tag1", "tag2"],
            "related_tags": {"tag1": ["tag2"]}
        }
    }
    
    result = semantic_analyzer.analyze_tags()
    assert result["success"] is True
    assert "tag_analysis" in result
    assert "most_used" in result["tag_analysis"]
    mock_storage.list_tags.assert_called_once()

def test_error_handling_analysis(semantic_analyzer, mock_model):
    """Test error handling during analysis."""
    mock_model.analyze.side_effect = Exception("Analysis error")
    
    result = semantic_analyzer.analyze_content("test content")
    assert result["success"] is False
    assert "error" in result

def test_batch_analyze(semantic_analyzer, mock_model):
    """Test batch analysis."""
    contents = ["content1", "content2"]
    mock_model.batch_analyze.return_value = {
        "success": True,
        "results": [
            {"topics": ["topic1"]},
            {"topics": ["topic2"]}
        ]
    }
    
    result = semantic_analyzer.batch_analyze(contents)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == len(contents)
    mock_model.batch_analyze.assert_called_once_with(contents)

def test_analyze_structure(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing note structure."""
    note_path = "notes/test.md"
    mock_storage.read_note.return_value = {
        "success": True,
        "content": "# Heading\n## Subheading\nContent"
    }
    mock_model.analyze_structure.return_value = {
        "success": True,
        "structure": {
            "headings": 2,
            "depth": 2,
            "sections": ["Heading", "Subheading"]
        }
    }
    
    result = semantic_analyzer.analyze_structure(note_path)
    assert result["success"] is True
    assert "structure" in result
    assert "headings" in result["structure"]
    mock_storage.read_note.assert_called_once_with(note_path)

def test_analyze_backlinks(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing backlinks."""
    note_path = "notes/test.md"
    mock_storage.get_backlinks.return_value = {
        "success": True,
        "backlinks": ["note1.md", "note2.md"]
    }
    mock_model.analyze_backlinks.return_value = {
        "success": True,
        "backlinks": ["note1.md", "note2.md"],
        "context": {
            "note1.md": "Reference context",
            "note2.md": "Another context"
        }
    }
    
    result = semantic_analyzer.analyze_backlinks(note_path)
    assert result["success"] is True
    assert "backlinks" in result
    assert "context" in result
    mock_storage.get_backlinks.assert_called_once_with(note_path)

def test_analyze_readability(semantic_analyzer, mock_model):
    """Test analyzing readability."""
    content = "Test content for readability analysis"
    mock_model.analyze_readability.return_value = {
        "success": True,
        "readability": {
            "score": 75,
            "grade_level": "8th",
            "complexity": "medium"
        }
    }
    
    result = semantic_analyzer.analyze_readability(content)
    assert result["success"] is True
    assert "readability" in result
    assert "score" in result["readability"]
    mock_model.analyze_readability.assert_called_once_with(content)

def test_get_statistics(semantic_analyzer, mock_model):
    """Test getting analysis statistics."""
    mock_model.get_statistics.return_value = {
        "success": True,
        "total_analyzed": 100,
        "average_complexity": "medium",
        "common_topics": ["topic1", "topic2"]
    }
    
    result = semantic_analyzer.get_statistics()
    assert result["success"] is True
    assert "total_analyzed" in result
    assert "average_complexity" in result
    mock_model.get_statistics.assert_called_once()

def test_analyze_vault_statistics(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing vault statistics."""
    mock_storage.get_vault_info.return_value = {
        "success": True,
        "info": {
            "total_notes": 100,
            "total_size": 1000000
        }
    }
    mock_model.analyze_vault_statistics.return_value = {
        "success": True,
        "statistics": {
            "total_notes": 100,
            "total_words": 50000,
            "average_note_length": 500,
            "topic_distribution": {
                "topic1": 30,
                "topic2": 20
            }
        }
    }
    
    result = semantic_analyzer.analyze_vault_statistics()
    assert result["success"] is True
    assert "statistics" in result
    assert "total_notes" in result["statistics"]
    mock_storage.get_vault_info.assert_called_once()

def test_analyze_note_network(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing note network."""
    mock_storage.list_notes.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md", "note3.md"]
    }
    mock_model.analyze_note_network.return_value = {
        "success": True,
        "network": {
            "nodes": ["note1", "note2", "note3"],
            "edges": [
                {"source": "note1", "target": "note2"},
                {"source": "note2", "target": "note3"}
            ],
            "clusters": [
                ["note1", "note2"],
                ["note3"]
            ]
        }
    }
    
    result = semantic_analyzer.analyze_note_network()
    assert result["success"] is True
    assert "network" in result
    assert "nodes" in result["network"]
    assert "edges" in result["network"]
    mock_storage.list_notes.assert_called_once()

def test_analyze_topic_evolution(semantic_analyzer, mock_storage, mock_model):
    """Test analyzing topic evolution."""
    start_date = "2024-01-01"
    end_date = "2024-03-14"
    mock_storage.list_notes_by_date.return_value = {
        "success": True,
        "notes": ["note1.md", "note2.md"]
    }
    mock_model.analyze_topic_evolution.return_value = {
        "success": True,
        "evolution": {
            "topics": ["topic1", "topic2"],
            "timeline": {
                "2024-01": {"topic1": 10, "topic2": 5},
                "2024-02": {"topic1": 8, "topic2": 7},
                "2024-03": {"topic1": 12, "topic2": 9}
            }
        }
    }
    
    result = semantic_analyzer.analyze_topic_evolution(start_date, end_date)
    assert result["success"] is True
    assert "evolution" in result
    assert "topics" in result["evolution"]
    assert "timeline" in result["evolution"]
    mock_storage.list_notes_by_date.assert_called_once_with(start_date, end_date) 
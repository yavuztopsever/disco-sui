import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.analysis.analysis_service import AnalysisService

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_semantic_analyzer():
    return MagicMock()

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def analysis_service(mock_context, mock_semantic_analyzer, mock_storage):
    service = AnalysisService(
        context=mock_context,
        semantic_analyzer=mock_semantic_analyzer,
        storage=mock_storage
    )
    service._semantic_analyzer = mock_semantic_analyzer
    return service

def test_service_initialization(analysis_service):
    """Test analysis service initialization."""
    assert analysis_service is not None
    assert analysis_service.context is not None
    assert analysis_service._semantic_analyzer is not None
    assert analysis_service.storage is not None

def test_analyze_content(analysis_service, mock_semantic_analyzer):
    """Test analyzing content."""
    content = "Test content for analysis"
    mock_semantic_analyzer.analyze_content.return_value = {
        "success": True,
        "analysis": {
            "topics": ["topic1", "topic2"],
            "sentiment": "positive",
            "key_phrases": ["phrase1", "phrase2"]
        }
    }
    
    result = analysis_service.analyze_content(content)
    assert result["success"] is True
    assert "analysis" in result
    assert "topics" in result["analysis"]
    mock_semantic_analyzer.analyze_content.assert_called_once_with(content)

def test_analyze_note(analysis_service, mock_semantic_analyzer):
    """Test analyzing a note."""
    note_path = "notes/test.md"
    mock_semantic_analyzer.analyze_note.return_value = {
        "success": True,
        "analysis": {
            "topics": ["topic1"],
            "references": ["ref1"],
            "complexity": "medium"
        }
    }
    
    result = analysis_service.analyze_note(note_path)
    assert result["success"] is True
    assert "analysis" in result
    assert "topics" in result["analysis"]
    mock_semantic_analyzer.analyze_note.assert_called_once_with(note_path)

def test_analyze_relationships(analysis_service, mock_semantic_analyzer):
    """Test analyzing relationships."""
    notes = ["note1.md", "note2.md"]
    mock_semantic_analyzer.analyze_relationships.return_value = {
        "success": True,
        "relationships": {
            "note1.md": ["note2.md"],
            "note2.md": ["note1.md"]
        }
    }
    
    result = analysis_service.analyze_relationships(notes)
    assert result["success"] is True
    assert "relationships" in result
    assert len(result["relationships"]) == len(notes)
    mock_semantic_analyzer.analyze_relationships.assert_called_once_with(notes)

def test_analyze_similarity(analysis_service, mock_semantic_analyzer):
    """Test analyzing similarity between notes."""
    note1 = "note1.md"
    note2 = "note2.md"
    mock_semantic_analyzer.analyze_similarity.return_value = {
        "success": True,
        "similarity": 0.85,
        "common_topics": ["topic1"]
    }
    
    result = analysis_service.analyze_similarity(note1, note2)
    assert result["success"] is True
    assert "similarity" in result
    assert "common_topics" in result
    mock_semantic_analyzer.analyze_similarity.assert_called_once_with(note1, note2)

def test_analyze_trends(analysis_service, mock_semantic_analyzer):
    """Test analyzing trends."""
    mock_semantic_analyzer.analyze_trends.return_value = {
        "success": True,
        "trends": {
            "topics": ["trending1", "trending2"],
            "time_periods": ["2024-03", "2024-02"]
        }
    }
    
    result = analysis_service.analyze_trends()
    assert result["success"] is True
    assert "trends" in result
    assert "topics" in result["trends"]
    mock_semantic_analyzer.analyze_trends.assert_called_once()

def test_generate_summary(analysis_service, mock_semantic_analyzer):
    """Test generating summary."""
    content = "Long content to summarize"
    mock_semantic_analyzer.generate_summary.return_value = {
        "success": True,
        "summary": "Short summary",
        "key_points": ["point1", "point2"]
    }
    
    result = analysis_service.generate_summary(content)
    assert result["success"] is True
    assert "summary" in result
    assert "key_points" in result
    mock_semantic_analyzer.generate_summary.assert_called_once_with(content)

def test_analyze_tags(analysis_service, mock_semantic_analyzer):
    """Test analyzing tags."""
    mock_semantic_analyzer.analyze_tags.return_value = {
        "success": True,
        "tag_analysis": {
            "most_used": ["tag1", "tag2"],
            "related_tags": {"tag1": ["tag2"]}
        }
    }
    
    result = analysis_service.analyze_tags()
    assert result["success"] is True
    assert "tag_analysis" in result
    assert "most_used" in result["tag_analysis"]
    mock_semantic_analyzer.analyze_tags.assert_called_once()

def test_error_handling_analysis(analysis_service, mock_semantic_analyzer):
    """Test error handling during analysis."""
    mock_semantic_analyzer.analyze_content.side_effect = Exception("Analysis error")
    
    result = analysis_service.analyze_content("test content")
    assert result["success"] is False
    assert "error" in result

def test_batch_analyze(analysis_service, mock_semantic_analyzer):
    """Test batch analysis."""
    contents = ["content1", "content2"]
    mock_semantic_analyzer.batch_analyze.return_value = {
        "success": True,
        "results": [
            {"topics": ["topic1"]},
            {"topics": ["topic2"]}
        ]
    }
    
    result = analysis_service.batch_analyze(contents)
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == len(contents)
    mock_semantic_analyzer.batch_analyze.assert_called_once_with(contents)

def test_analyze_structure(analysis_service, mock_semantic_analyzer):
    """Test analyzing note structure."""
    note_path = "notes/test.md"
    mock_semantic_analyzer.analyze_structure.return_value = {
        "success": True,
        "structure": {
            "headings": 3,
            "depth": 2,
            "sections": ["section1", "section2"]
        }
    }
    
    result = analysis_service.analyze_structure(note_path)
    assert result["success"] is True
    assert "structure" in result
    assert "headings" in result["structure"]
    mock_semantic_analyzer.analyze_structure.assert_called_once_with(note_path)

def test_get_analysis_statistics(analysis_service, mock_semantic_analyzer):
    """Test getting analysis statistics."""
    mock_semantic_analyzer.get_statistics.return_value = {
        "success": True,
        "total_analyzed": 100,
        "average_complexity": "medium",
        "common_topics": ["topic1", "topic2"]
    }
    
    result = analysis_service.get_statistics()
    assert result["success"] is True
    assert "total_analyzed" in result
    assert "average_complexity" in result
    mock_semantic_analyzer.get_statistics.assert_called_once()

def test_analyze_backlinks(analysis_service, mock_semantic_analyzer):
    """Test analyzing backlinks."""
    note_path = "notes/test.md"
    mock_semantic_analyzer.analyze_backlinks.return_value = {
        "success": True,
        "backlinks": ["note1.md", "note2.md"],
        "context": {
            "note1.md": "Reference context",
            "note2.md": "Another context"
        }
    }
    
    result = analysis_service.analyze_backlinks(note_path)
    assert result["success"] is True
    assert "backlinks" in result
    assert "context" in result
    mock_semantic_analyzer.analyze_backlinks.assert_called_once_with(note_path)

def test_analyze_readability(analysis_service, mock_semantic_analyzer):
    """Test analyzing readability."""
    content = "Test content for readability analysis"
    mock_semantic_analyzer.analyze_readability.return_value = {
        "success": True,
        "readability": {
            "score": 75,
            "grade_level": "8th",
            "complexity": "medium"
        }
    }
    
    result = analysis_service.analyze_readability(content)
    assert result["success"] is True
    assert "readability" in result
    assert "score" in result["readability"]
    mock_semantic_analyzer.analyze_readability.assert_called_once_with(content)

def test_get_service_config(analysis_service):
    """Test getting service configuration."""
    result = analysis_service.get_config()
    assert result["success"] is True
    assert "config" in result
    assert isinstance(result["config"], dict)

def test_update_service_config(analysis_service):
    """Test updating service configuration."""
    config_update = {
        "analysis_depth": "deep",
        "max_tokens": 1000,
        "include_metadata": True
    }
    
    result = analysis_service.update_config(config_update)
    assert result["success"] is True
    assert result["config"] == config_update

def test_analyze_vault_statistics(analysis_service, mock_semantic_analyzer):
    """Test analyzing vault statistics."""
    mock_semantic_analyzer.analyze_vault_statistics.return_value = {
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
    
    result = analysis_service.analyze_vault_statistics()
    assert result["success"] is True
    assert "statistics" in result
    assert "total_notes" in result["statistics"]
    mock_semantic_analyzer.analyze_vault_statistics.assert_called_once()

def test_analyze_note_network(analysis_service, mock_semantic_analyzer):
    """Test analyzing note network."""
    mock_semantic_analyzer.analyze_note_network.return_value = {
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
    
    result = analysis_service.analyze_note_network()
    assert result["success"] is True
    assert "network" in result
    assert "nodes" in result["network"]
    assert "edges" in result["network"]
    mock_semantic_analyzer.analyze_note_network.assert_called_once()

def test_analyze_topic_evolution(analysis_service, mock_semantic_analyzer):
    """Test analyzing topic evolution."""
    start_date = "2024-01-01"
    end_date = "2024-03-14"
    mock_semantic_analyzer.analyze_topic_evolution.return_value = {
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
    
    result = analysis_service.analyze_topic_evolution(start_date, end_date)
    assert result["success"] is True
    assert "evolution" in result
    assert "topics" in result["evolution"]
    assert "timeline" in result["evolution"]
    mock_semantic_analyzer.analyze_topic_evolution.assert_called_once_with(start_date, end_date) 
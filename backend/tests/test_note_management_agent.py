import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
from datetime import datetime
from src.agents.NoteManagementAgent import NoteManagementAgent, NoteRequest
from src.core.exceptions import NoteManagementError

@pytest.fixture
def mock_vault_path():
    return "/test/vault/path"

@pytest.fixture
def mock_rag():
    return Mock()

@pytest.fixture
def mock_indexer():
    return Mock()

@pytest.fixture
def mock_semantic_analyzer():
    return Mock()

@pytest.fixture
def mock_llm_model():
    return AsyncMock()

@pytest.fixture
async def note_management_agent(mock_vault_path, mock_rag, mock_indexer, mock_semantic_analyzer, mock_llm_model):
    with patch("src.agents.NoteManagementAgent.RAG", return_value=mock_rag), \
         patch("src.agents.NoteManagementAgent.Indexer", return_value=mock_indexer), \
         patch("src.agents.NoteManagementAgent.SemanticAnalyzer", return_value=mock_semantic_analyzer), \
         patch("src.agents.NoteManagementAgent.LiteLLMModel", return_value=mock_llm_model), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        agent = NoteManagementAgent(mock_vault_path)
        yield agent

@pytest.mark.asyncio
async def test_initialization(note_management_agent, mock_vault_path):
    """Test agent initialization."""
    assert note_management_agent.vault_path == mock_vault_path
    assert note_management_agent.plugin_path == os.path.join(mock_vault_path, '.obsidian', 'plugins', 'discosui')
    assert note_management_agent.tool_usage_stats == {}

@pytest.mark.asyncio
async def test_process_message_question_intent(note_management_agent, mock_llm_model):
    """Test processing a question message."""
    # Mock intent analysis response
    mock_llm_model.generate.return_value.json.return_value = {
        "intent": "question",
        "parameters": {
            "title": None,
            "content": None,
            "folder": None,
            "tags": [],
            "template": None
        },
        "context": "test context",
        "auto_open_notes": [],
        "recommended_tools": ["rag_query"],
        "potential_errors": []
    }

    # Mock RAG response
    note_management_agent.rag.process_query.return_value.dict.return_value = {
        "success": True,
        "response": "Test response",
        "notes_to_open": []
    }

    result = await note_management_agent.process_message("What is the capital of France?")
    assert result["success"] is True
    assert "response" in result
    assert result["context"] == "test context"

@pytest.mark.asyncio
async def test_process_message_create_note(note_management_agent, mock_llm_model):
    """Test processing a create note message."""
    # Mock intent analysis response
    mock_llm_model.generate.return_value.json.return_value = {
        "intent": "create",
        "parameters": {
            "title": "Test Note",
            "content": "Test content",
            "folder": None,
            "tags": [],
            "template": None
        },
        "context": "test context",
        "auto_open_notes": [],
        "recommended_tools": ["create_note"],
        "potential_errors": []
    }

    # Mock tool response
    create_note_tool = next(t for t in note_management_agent.tools if t.name == "create_note")
    create_note_tool.forward = AsyncMock(return_value={
        "success": True,
        "message": "Note created successfully"
    })

    result = await note_management_agent.process_message("Create a new note titled 'Test Note' with content 'Test content'")
    assert result["success"] is True
    assert "response" in result
    assert result["context"] == "test context"

@pytest.mark.asyncio
async def test_process_message_error(note_management_agent, mock_llm_model):
    """Test error handling in message processing."""
    mock_llm_model.generate.side_effect = Exception("Test error")

    result = await note_management_agent.process_message("Test message")
    assert result["success"] is False
    assert "error" in result
    assert "Test error" in result["error"]

@pytest.mark.asyncio
async def test_tool_usage_tracking(note_management_agent):
    """Test tool usage statistics tracking."""
    note_management_agent._track_tool_usage("test_tool", True)
    stats = note_management_agent.get_tool_usage_stats()
    
    assert "test_tool" in stats
    assert stats["test_tool"]["total_calls"] == 1
    assert stats["test_tool"]["successful_calls"] == 1
    assert stats["test_tool"]["failed_calls"] == 0

    note_management_agent._track_tool_usage("test_tool", False, "Test error")
    stats = note_management_agent.get_tool_usage_stats()
    
    assert stats["test_tool"]["total_calls"] == 2
    assert stats["test_tool"]["successful_calls"] == 1
    assert stats["test_tool"]["failed_calls"] == 1
    assert "Test error" in stats["test_tool"]["common_errors"]

@pytest.mark.asyncio
async def test_run(note_management_agent):
    """Test the run method."""
    with patch.object(note_management_agent, "process_message", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {"success": True, "response": "Test response"}
        
        result = await note_management_agent.run("Test task")
        assert result["success"] is True
        assert result["response"] == "Test response"
        mock_process.assert_called_once_with("Test task")

@pytest.mark.asyncio
async def test_run_error(note_management_agent):
    """Test error handling in the run method."""
    with patch.object(note_management_agent, "process_message", new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Test error")
        
        result = await note_management_agent.run("Test task")
        assert result["success"] is False
        assert "Test error" in result["error"]

@pytest.mark.asyncio
async def test_format_response(note_management_agent, mock_llm_model):
    """Test response formatting."""
    mock_llm_model.generate.return_value = "Formatted response"
    
    result = note_management_agent._format_response(
        {"success": True, "data": "test data"},
        "test context"
    )
    
    assert result["success"] is True
    assert result["response"] == "Formatted response"
    assert result["context"] == "test context"
    assert result["data"] == {"success": True, "data": "test data"}

@pytest.mark.asyncio
async def test_format_error_response(note_management_agent):
    """Test error response formatting."""
    result = note_management_agent._format_error_response("Test error", "test context")
    
    assert result["success"] is False
    assert result["error"] == "Test error"
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0 
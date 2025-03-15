"""Integration tests for the main application flow.

This module contains comprehensive integration tests for the DiscoSui application's main flows,
including question processing, action processing, tool execution, and response handling.
"""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import json

from src.core.config import Settings
from src.core.tool_manager import ToolManager
from src.core.obsidian_utils import ObsidianUtils
from src.services.analysis.rag_service import RAGService
from src.services.content.chat_interface import ChatInterface
from src.core.exceptions import (
    NoteNotFoundError,
    ToolExecutionError,
    RAGError,
    InvalidInputError
)

# Test Data
SAMPLE_NOTES = {
    "test_note.md": """# Test Note
This is a test note with some content.
## Section 1
Content in section 1.
## Section 2
Content in section 2.""",
    
    "python.md": """# Python
Python is a programming language.
## Key Features
- Easy to learn
- Large ecosystem
- Great for AI/ML""",
    
    "meeting.md": """# Meeting Notes
Discussion about project goals.
## Action Items
1. Complete documentation
2. Add more tests
3. Review code""",
    
    "template.md": """---
type: note
tags: [test, template]
created: {{date}}
---
# {{title}}
{{content}}
"""
}

@pytest.fixture
def test_vault(tmp_path) -> Path:
    """Create a test vault with sample notes.
    
    Args:
        tmp_path: Pytest fixture providing temporary directory path.
        
    Returns:
        Path: Path to the created test vault.
    """
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    
    # Create sample notes
    for filename, content in SAMPLE_NOTES.items():
        note_path = vault_path / filename
        note_path.write_text(content)
    
    return vault_path

@pytest.fixture
def test_environment(tmp_path, test_vault) -> Dict[str, Path]:
    """Set up test environment with necessary directories and configurations.
    
    Args:
        tmp_path: Pytest fixture providing temporary directory path.
        test_vault: Fixture providing test vault path.
        
    Returns:
        Dict[str, Path]: Dictionary containing paths for vault and vector database.
    """
    # Create necessary directories
    vector_db_path = tmp_path / "vector_db"
    vector_db_path.mkdir()
    
    return {
        "vault_path": test_vault,
        "vector_db_path": vector_db_path
    }

@pytest.fixture
async def initialized_services(test_environment):
    """Initialize and return all required services.
    
    Args:
        test_environment: Fixture providing test environment paths.
        
    Returns:
        tuple: Tuple containing initialized services (settings, obsidian_utils, rag_service, tool_manager, chat_interface)
    """
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        RAG_VECTOR_DB_PATH=str(test_environment["vector_db_path"]),
        RAG_CHUNK_SIZE=500,
        RAG_CHUNK_OVERLAP=50
    )
    
    obsidian_utils = ObsidianUtils()
    rag_service = RAGService()
    tool_manager = ToolManager()
    chat_interface = ChatInterface()
    
    # Initialize services
    await asyncio.gather(
        rag_service.initialize(settings),
        tool_manager.initialize(settings)
    )
    
    return settings, obsidian_utils, rag_service, tool_manager, chat_interface

@pytest.mark.asyncio
async def test_question_processing_flow_success(test_environment, initialized_services):
    """Test successful question processing flow."""
    _, _, rag_service, _, chat_interface = initialized_services
    
    # Test various questions
    test_cases = [
        {
            "question": "What is Python?",
            "expected_keywords": ["Python", "programming language"],
            "expected_context_size": 1
        },
        {
            "question": "What are Python's key features?",
            "expected_keywords": ["Easy to learn", "Large ecosystem", "AI/ML"],
            "expected_context_size": 1
        },
        {
            "question": "What are the action items from the meeting?",
            "expected_keywords": ["documentation", "tests", "code"],
            "expected_context_size": 1
        }
    ]
    
    for case in test_cases:
        response = await chat_interface.process_question(case["question"])
        context = await rag_service.get_context(case["question"])
        
        # Verify response
        assert response is not None
        for keyword in case["expected_keywords"]:
            assert keyword in response
            
        # Verify context
        assert len(context) >= case["expected_context_size"]
        assert any(keyword in "".join(context) for keyword in case["expected_keywords"])

@pytest.mark.asyncio
async def test_question_processing_flow_errors(test_environment, initialized_services):
    """Test error handling in question processing flow."""
    _, _, _, _, chat_interface = initialized_services
    
    # Test with empty question
    with pytest.raises(InvalidInputError):
        await chat_interface.process_question("")
    
    # Test with None question
    with pytest.raises(InvalidInputError):
        await chat_interface.process_question(None)
    
    # Test with very long question
    long_question = "test " * 1000
    with pytest.raises(InvalidInputError):
        await chat_interface.process_question(long_question)

@pytest.mark.asyncio
async def test_action_processing_flow_success(test_environment, initialized_services):
    """Test successful action processing flow."""
    settings, _, _, tool_manager, chat_interface = initialized_services
    
    test_cases = [
        {
            "action": "Create a new note titled 'Test Action'",
            "verify_file": "Test Action.md",
            "expected_content": ["Test Action"]
        },
        {
            "action": "Create a note about Python with template",
            "verify_file": "Python Note.md",
            "expected_content": ["Python", "type: note", "tags:"]
        }
    ]
    
    for case in test_cases:
        response = await chat_interface.process_action(case["action"])
        
        # Verify response
        assert response is not None
        assert "created" in response.lower()
        
        # Verify note creation
        note_path = Path(settings.VAULT_PATH) / case["verify_file"]
        assert note_path.exists()
        content = note_path.read_text()
        for expected in case["expected_content"]:
            assert expected in content

@pytest.mark.asyncio
async def test_action_processing_flow_errors(test_environment, initialized_services):
    """Test error handling in action processing flow."""
    _, _, _, _, chat_interface = initialized_services
    
    # Test with empty action
    with pytest.raises(InvalidInputError):
        await chat_interface.process_action("")
    
    # Test with None action
    with pytest.raises(InvalidInputError):
        await chat_interface.process_action(None)
    
    # Test with invalid action
    with pytest.raises(ToolExecutionError):
        await chat_interface.process_action("Invalid action that doesn't exist")

@pytest.mark.asyncio
async def test_tool_execution_flow_success(test_environment, initialized_services):
    """Test successful tool execution flow."""
    settings, _, _, tool_manager, _ = initialized_services
    
    test_cases = [
        {
            "tool_name": "create_note",
            "parameters": {
                "title": "Tool Test Note",
                "content": "This is a test note created by a tool.",
                "template": None
            }
        },
        {
            "tool_name": "create_note",
            "parameters": {
                "title": "Template Note",
                "content": "Content with template",
                "template": "template.md"
            }
        }
    ]
    
    for case in test_cases:
        result = await tool_manager.execute_tool(case)
        
        # Verify tool execution
        assert result is not None
        assert result.success is True
        
        # Verify note creation
        note_path = Path(settings.VAULT_PATH) / f"{case['parameters']['title']}.md"
        assert note_path.exists()
        content = note_path.read_text().lower()
        assert case['parameters']['content'].lower() in content
        
        if case['parameters']['template']:
            assert "type: note" in content
            assert "tags:" in content

@pytest.mark.asyncio
async def test_tool_execution_flow_errors(test_environment, initialized_services):
    """Test error handling in tool execution flow."""
    _, _, _, tool_manager, _ = initialized_services
    
    # Test with invalid tool name
    with pytest.raises(ToolExecutionError):
        await tool_manager.execute_tool({
            "tool_name": "invalid_tool",
            "parameters": {}
        })
    
    # Test with missing required parameters
    with pytest.raises(InvalidInputError):
        await tool_manager.execute_tool({
            "tool_name": "create_note",
            "parameters": {}
        })
    
    # Test with invalid template
    with pytest.raises(NoteNotFoundError):
        await tool_manager.execute_tool({
            "tool_name": "create_note",
            "parameters": {
                "title": "Invalid Template Note",
                "content": "Content",
                "template": "non_existent_template.md"
            }
        })

@pytest.mark.asyncio
async def test_response_handling_flow_success(test_environment, initialized_services):
    """Test successful response handling flow."""
    _, _, _, _, chat_interface = initialized_services
    
    test_cases = [
        {
            "response": {
                "content": "This is a test response",
                "citations": ["test_note.md", "python.md"],
                "relevant_notes": ["meeting.md"]
            },
            "expected_notes": 1
        },
        {
            "response": {
                "content": "Response with multiple notes",
                "citations": ["test_note.md", "python.md", "meeting.md"],
                "relevant_notes": ["test_note.md", "python.md"]
            },
            "expected_notes": 2
        }
    ]
    
    for case in test_cases:
        formatted_response = await chat_interface.format_response(case["response"])
        
        # Verify response formatting
        assert formatted_response is not None
        assert case["response"]["content"] in formatted_response
        assert all(note in formatted_response for note in case["response"]["citations"])
        
        # Verify note opening
        opened_notes = await chat_interface.open_relevant_notes(case["response"]["relevant_notes"])
        assert opened_notes is not None
        assert len(opened_notes) == case["expected_notes"]

@pytest.mark.asyncio
async def test_response_handling_flow_errors(test_environment, initialized_services):
    """Test error handling in response handling flow."""
    _, _, _, _, chat_interface = initialized_services
    
    # Test with invalid response format
    with pytest.raises(InvalidInputError):
        await chat_interface.format_response({})
    
    # Test with non-existent notes
    with pytest.raises(NoteNotFoundError):
        await chat_interface.open_relevant_notes(["non_existent_note.md"])
    
    # Test with None response
    with pytest.raises(InvalidInputError):
        await chat_interface.format_response(None)

@pytest.mark.asyncio
async def test_performance(test_environment, initialized_services):
    """Test performance of main flows."""
    _, _, rag_service, tool_manager, chat_interface = initialized_services
    
    # Test RAG performance
    start_time = datetime.now()
    await chat_interface.process_question("What is Python?")
    rag_time = (datetime.now() - start_time).total_seconds()
    assert rag_time < 2.0  # RAG should complete within 2 seconds
    
    # Test tool execution performance
    start_time = datetime.now()
    await tool_manager.execute_tool({
        "tool_name": "create_note",
        "parameters": {
            "title": "Performance Test Note",
            "content": "Testing tool execution performance"
        }
    })
    tool_time = (datetime.now() - start_time).total_seconds()
    assert tool_time < 1.0  # Tool execution should complete within 1 second
    
    # Test response formatting performance
    start_time = datetime.now()
    await chat_interface.format_response({
        "content": "Performance test response",
        "citations": ["test_note.md"],
        "relevant_notes": ["meeting.md"]
    })
    format_time = (datetime.now() - start_time).total_seconds()
    assert format_time < 0.5  # Response formatting should complete within 0.5 seconds 
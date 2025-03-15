"""End-to-end tests for the smallagents plugin functionality."""

import pytest
import os
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.NoteManagementAgent import NoteManagementAgent
from src.core.exceptions import (
    NoteNotFoundError,
    NoteAlreadyExistsError,
    TemplateNotFoundError,
    FrontmatterError,
    NoteManagementError
)

@pytest.fixture
async def test_vault(tmp_path) -> Path:
    """Create a temporary test vault."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    
    # Create basic vault structure
    (vault_path / ".obsidian").mkdir()
    (vault_path / ".obsidian" / "plugins").mkdir()
    (vault_path / "templates").mkdir()
    (vault_path / "audio").mkdir()
    (vault_path / "emails").mkdir()
    
    return vault_path

@pytest.fixture
async def note_management_agent(test_vault) -> NoteManagementAgent:
    """Create a NoteManagementAgent instance."""
    agent = NoteManagementAgent(str(test_vault))
    return agent

@pytest.mark.asyncio
class TestSmallAgentsPlugin:
    """Test suite for smallagents plugin functionality."""
    
    async def test_agent_initialization(self, note_management_agent, test_vault):
        """Test agent initialization and basic setup."""
        # Verify agent attributes
        assert note_management_agent.vault_path == str(test_vault)
        assert note_management_agent.plugin_path == str(test_vault / ".obsidian" / "plugins" / "discosui")
        assert note_management_agent.tool_usage_stats == {}
        
        # Verify plugin setup
        assert (test_vault / ".obsidian" / "plugins" / "discosui").exists()
        assert (test_vault / ".obsidian" / "plugins" / "discosui" / "manifest.json").exists()
    
    async def test_note_management_tools(self, note_management_agent, test_vault):
        """Test note management tools."""
        # Test note creation
        create_result = await note_management_agent.process_message(
            "Create a new note titled 'Test Note' with content 'This is a test note'"
        )
        assert create_result["success"] is True
        assert (test_vault / "Test Note.md").exists()
        
        # Test note update
        update_result = await note_management_agent.process_message(
            "Update the note 'Test Note' to say 'This is an updated test note'"
        )
        assert update_result["success"] is True
        assert "updated" in (test_vault / "Test Note.md").read_text()
        
        # Test note search
        search_result = await note_management_agent.process_message(
            "Find all notes containing the word 'test'"
        )
        assert search_result["success"] is True
        assert "Test Note" in str(search_result)
        
        # Test note deletion
        delete_result = await note_management_agent.process_message(
            "Delete the note 'Test Note'"
        )
        assert delete_result["success"] is True
        assert not (test_vault / "Test Note.md").exists()
    
    async def test_folder_management_tools(self, note_management_agent, test_vault):
        """Test folder management tools."""
        # Test folder creation
        create_result = await note_management_agent.process_message(
            "Create a new folder called 'Projects'"
        )
        assert create_result["success"] is True
        assert (test_vault / "Projects").exists()
        
        # Test folder movement
        move_result = await note_management_agent.process_message(
            "Move the folder 'Projects' to 'Work/Projects'"
        )
        assert move_result["success"] is True
        assert (test_vault / "Work" / "Projects").exists()
        
        # Test folder deletion
        delete_result = await note_management_agent.process_message(
            "Delete the folder 'Work/Projects'"
        )
        assert delete_result["success"] is True
        assert not (test_vault / "Work" / "Projects").exists()
    
    async def test_tag_management_tools(self, note_management_agent, test_vault):
        """Test tag management tools."""
        # Create a note with tags
        create_result = await note_management_agent.process_message(
            "Create a new note titled 'Tagged Note' with tags #project and #important"
        )
        assert create_result["success"] is True
        
        # Verify tags in frontmatter
        note_content = (test_vault / "Tagged Note.md").read_text()
        assert "#project" in note_content
        assert "#important" in note_content
        
        # Test tag search
        search_result = await note_management_agent.process_message(
            "Find all notes with the tag #project"
        )
        assert search_result["success"] is True
        assert "Tagged Note" in str(search_result)
    
    async def test_template_management_tools(self, note_management_agent, test_vault):
        """Test template management tools."""
        # Create a template
        template_result = await note_management_agent.process_message(
            "Create a new template called 'Meeting Notes' with content '# Meeting: {{title}}\\nDate: {{date}}\\nAttendees: {{attendees}}'"
        )
        assert template_result["success"] is True
        
        # Use the template
        note_result = await note_management_agent.process_message(
            "Create a new note using the 'Meeting Notes' template with title 'Team Sync', date 'today', and attendees 'Alice, Bob'"
        )
        assert note_result["success"] is True
        assert (test_vault / "Team Sync.md").exists()
        note_content = (test_vault / "Team Sync.md").read_text()
        assert "Team Sync" in note_content
        assert "Alice, Bob" in note_content
    
    async def test_audio_processing_tools(self, note_management_agent, test_vault):
        """Test audio processing tools."""
        # Create a mock audio file
        audio_file = test_vault / "audio" / "test_recording.mp3"
        audio_file.write_bytes(b"mock audio data")
        
        # Test audio transcription
        transcribe_result = await note_management_agent.process_message(
            "Transcribe the audio file 'test_recording.mp3'"
        )
        assert transcribe_result["success"] is True
        assert (test_vault / "Transcriptions" / "test_recording.md").exists()
    
    async def test_email_processing_tools(self, note_management_agent, test_vault):
        """Test email processing tools."""
        # Create a mock email file
        email_file = test_vault / "emails" / "test_email.eml"
        email_file.write_text("From: test@example.com\nSubject: Test Email\n\nThis is a test email.")
        
        # Test email processing
        process_result = await note_management_agent.process_message(
            "Process the email file 'test_email.eml'"
        )
        assert process_result["success"] is True
        assert (test_vault / "Emails" / "Test Email.md").exists()
    
    async def test_semantic_analysis_tools(self, note_management_agent, test_vault):
        """Test semantic analysis tools."""
        # Create some test notes
        await note_management_agent.process_message(
            "Create a note titled 'Python Programming' with content 'Python is a versatile programming language.'"
        )
        await note_management_agent.process_message(
            "Create a note titled 'Programming Languages' with content 'There are many programming languages like Python, Java, and JavaScript.'"
        )
        
        # Test finding related notes
        related_result = await note_management_agent.process_message(
            "Find notes related to 'Python Programming'"
        )
        assert related_result["success"] is True
        assert "Programming Languages" in str(related_result)
    
    async def test_vault_organization_tools(self, note_management_agent, test_vault):
        """Test vault organization tools."""
        # Create some test notes and folders
        await note_management_agent.process_message("Create a folder structure for a programming project")
        
        # Test vault analysis
        analysis_result = await note_management_agent.process_message(
            "Analyze the vault structure and suggest improvements"
        )
        assert analysis_result["success"] is True
        assert "suggestions" in analysis_result
    
    async def test_hierarchy_management_tools(self, note_management_agent, test_vault):
        """Test hierarchy management tools."""
        # Create a hierarchical structure
        hierarchy_result = await note_management_agent.process_message(
            "Create a hierarchical structure for a software project with sections for documentation, source code, and tests"
        )
        assert hierarchy_result["success"] is True
        assert (test_vault / "Software Project").exists()
        assert (test_vault / "Software Project" / "Documentation").exists()
        assert (test_vault / "Software Project" / "Source Code").exists()
        assert (test_vault / "Software Project" / "Tests").exists()
    
    async def test_error_handling(self, note_management_agent, test_vault):
        """Test error handling in various scenarios."""
        # Test non-existent note
        error_result = await note_management_agent.process_message(
            "Update the note 'Non-existent Note' with content 'This should fail'"
        )
        assert error_result["success"] is False
        assert "not found" in str(error_result["error"]).lower()
        
        # Test invalid template
        error_result = await note_management_agent.process_message(
            "Create a note using the non-existent template 'Invalid Template'"
        )
        assert error_result["success"] is False
        assert "template" in str(error_result["error"]).lower()
        
        # Test invalid folder operations
        error_result = await note_management_agent.process_message(
            "Move the non-existent folder 'Invalid' to 'New Location'"
        )
        assert error_result["success"] is False
        assert "folder" in str(error_result["error"]).lower()
    
    async def test_tool_usage_tracking(self, note_management_agent):
        """Test tool usage tracking functionality."""
        # Perform some operations
        await note_management_agent.process_message(
            "Create a new note titled 'Usage Test' with content 'Testing tool usage tracking'"
        )
        
        # Check tool usage stats
        stats = note_management_agent.get_tool_usage_stats()
        assert "create_note" in stats
        assert stats["create_note"]["total_calls"] > 0
        assert stats["create_note"]["successful_calls"] > 0
    
    async def test_concurrent_operations(self, note_management_agent, test_vault):
        """Test handling of concurrent operations."""
        # Create multiple concurrent requests
        tasks = [
            note_management_agent.process_message(f"Create a note titled 'Concurrent Note {i}'")
            for i in range(5)
        ]
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        assert all(result["success"] for result in results)
        assert all((test_vault / f"Concurrent Note {i}.md").exists() for i in range(5))
    
    async def test_service_integration(self, note_management_agent):
        """Test integration with various services."""
        # Test RAG service
        rag_result = await note_management_agent.process_message(
            "What are the main topics discussed in my notes?"
        )
        assert rag_result["success"] is True
        
        # Test indexing service
        index_result = await note_management_agent.process_message(
            "Reindex the vault"
        )
        assert index_result["success"] is True
        
        # Test semantic analysis service
        analysis_result = await note_management_agent.process_message(
            "Generate a knowledge graph of my notes"
        )
        assert analysis_result["success"] is True 
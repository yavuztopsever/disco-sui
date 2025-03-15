"""End-to-end tests for smallagents and Obsidian plugin integration."""

import pytest
import os
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.NoteManagementAgent import NoteManagementAgent
from src.core.exceptions import (
    NoteManagementError,
    PluginError,
    IntegrationError
)
from src.services.plugin.plugin_manager import PluginManager
from src.services.plugin.plugin_loader import PluginLoader

@pytest.fixture
async def test_vault(tmp_path) -> Path:
    """Create a temporary test vault."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    
    # Create basic vault structure
    (vault_path / ".obsidian").mkdir()
    (vault_path / ".obsidian" / "plugins").mkdir()
    (vault_path / "templates").mkdir()
    
    return vault_path

@pytest.fixture
async def plugin_manager(test_vault) -> PluginManager:
    """Create a PluginManager instance."""
    manager = PluginManager()
    await manager.initialize(test_vault)
    return manager

@pytest.fixture
async def note_management_agent(test_vault) -> NoteManagementAgent:
    """Create a NoteManagementAgent instance."""
    agent = NoteManagementAgent(str(test_vault))
    return agent

@pytest.mark.asyncio
class TestPluginIntegration:
    """Test suite for smallagents and Obsidian plugin integration."""
    
    async def test_plugin_initialization(self, plugin_manager, test_vault):
        """Test plugin initialization and setup."""
        # Verify plugin directory structure
        plugin_dir = test_vault / ".obsidian" / "plugins" / "discosui"
        assert plugin_dir.exists()
        assert (plugin_dir / "manifest.json").exists()
        assert (plugin_dir / "main.js").exists()
        assert (plugin_dir / "styles.css").exists()
        
        # Verify plugin registration
        plugins = await plugin_manager.list_plugins()
        assert "discosui" in plugins
        assert plugins["discosui"]["enabled"] is True
    
    async def test_plugin_manifest(self, plugin_manager, test_vault):
        """Test plugin manifest configuration."""
        manifest_path = test_vault / ".obsidian" / "plugins" / "discosui" / "manifest.json"
        
        # Read and verify manifest content
        import json
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest["id"] == "discosui"
        assert manifest["name"] == "DiscoSui"
        assert manifest["version"] == "1.0.0"
        assert manifest["minAppVersion"] == "0.15.0"
        assert not manifest["isDesktopOnly"]
    
    async def test_plugin_api_integration(self, plugin_manager, note_management_agent):
        """Test integration between plugin API and agent."""
        # Test API command registration
        commands = await plugin_manager.get_commands("discosui")
        assert "process_message" in commands
        assert "get_tool_usage_stats" in commands
        
        # Test API command execution
        result = await plugin_manager.execute_command(
            "discosui",
            "process_message",
            {"message": "Create a new note titled 'API Test'"}
        )
        assert result["success"] is True
    
    async def test_plugin_settings(self, plugin_manager):
        """Test plugin settings management."""
        # Update plugin settings
        settings = {
            "openai_api_key": "test_key",
            "model": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        update_result = await plugin_manager.update_plugin_settings(
            "discosui",
            settings
        )
        assert update_result["success"] is True
        
        # Verify settings
        current_settings = await plugin_manager.get_plugin_settings("discosui")
        assert current_settings["openai_api_key"] == "test_key"
        assert current_settings["model"] == "gpt-4"
    
    async def test_plugin_event_handling(self, plugin_manager, note_management_agent):
        """Test plugin event handling."""
        # Register test event handler
        test_events = []
        
        async def test_handler(event_data):
            test_events.append(event_data)
        
        await plugin_manager.register_event_handler(
            "discosui",
            "note-created",
            test_handler
        )
        
        # Trigger event
        await note_management_agent.process_message(
            "Create a new note titled 'Event Test'"
        )
        
        # Verify event was handled
        assert len(test_events) == 1
        assert test_events[0]["note_title"] == "Event Test"
    
    async def test_plugin_ribbon_integration(self, plugin_manager):
        """Test plugin ribbon icon integration."""
        # Get ribbon items
        ribbon_items = await plugin_manager.get_ribbon_items("discosui")
        
        # Verify DiscoSui ribbon item
        assert any(item["id"] == "discosui-chat" for item in ribbon_items)
        
        # Test ribbon item click
        result = await plugin_manager.trigger_ribbon_action(
            "discosui",
            "discosui-chat"
        )
        assert result["success"] is True
    
    async def test_plugin_commands_integration(self, plugin_manager):
        """Test plugin commands integration."""
        # Get plugin commands
        commands = await plugin_manager.get_commands("discosui")
        
        # Verify essential commands
        assert "open-chat" in commands
        assert "process-message" in commands
        assert "show-stats" in commands
        
        # Test command execution
        result = await plugin_manager.execute_command(
            "discosui",
            "open-chat"
        )
        assert result["success"] is True
    
    async def test_plugin_view_integration(self, plugin_manager):
        """Test plugin view integration."""
        # Register test view
        view_result = await plugin_manager.register_view(
            "discosui",
            "chat-view",
            {
                "type": "leaf",
                "icon": "message-square",
                "title": "DiscoSui Chat"
            }
        )
        assert view_result["success"] is True
        
        # Get registered views
        views = await plugin_manager.get_views("discosui")
        assert "chat-view" in views
    
    async def test_plugin_error_handling(self, plugin_manager, note_management_agent):
        """Test plugin error handling."""
        # Test invalid command
        error_result = await plugin_manager.execute_command(
            "discosui",
            "invalid-command"
        )
        assert error_result["success"] is False
        assert "command not found" in str(error_result["error"]).lower()
        
        # Test invalid settings
        error_result = await plugin_manager.update_plugin_settings(
            "discosui",
            {"invalid_setting": "value"}
        )
        assert error_result["success"] is False
        assert "invalid setting" in str(error_result["error"]).lower()
    
    async def test_plugin_state_persistence(self, plugin_manager):
        """Test plugin state persistence."""
        # Set plugin state
        state = {
            "chat_history": [
                {"role": "user", "content": "Test message"},
                {"role": "assistant", "content": "Test response"}
            ],
            "tool_usage": {"create_note": {"total_calls": 5}}
        }
        
        save_result = await plugin_manager.save_plugin_state(
            "discosui",
            state
        )
        assert save_result["success"] is True
        
        # Load and verify state
        loaded_state = await plugin_manager.load_plugin_state("discosui")
        assert loaded_state["chat_history"] == state["chat_history"]
        assert loaded_state["tool_usage"] == state["tool_usage"]
    
    async def test_plugin_updates(self, plugin_manager):
        """Test plugin update handling."""
        # Check for updates
        update_info = await plugin_manager.check_for_updates("discosui")
        assert "current_version" in update_info
        assert "latest_version" in update_info
        assert "update_available" in update_info
        
        if update_info["update_available"]:
            # Test update process
            update_result = await plugin_manager.update_plugin("discosui")
            assert update_result["success"] is True
            assert update_result["new_version"] == update_info["latest_version"]
    
    async def test_plugin_dependency_management(self, plugin_manager):
        """Test plugin dependency management."""
        # Get plugin dependencies
        deps = await plugin_manager.get_plugin_dependencies("discosui")
        assert "smolagents" in deps
        
        # Check dependency status
        status = await plugin_manager.check_dependencies("discosui")
        assert status["success"] is True
        assert all(dep["installed"] for dep in status["dependencies"])
    
    async def test_plugin_resource_management(self, plugin_manager, test_vault):
        """Test plugin resource management."""
        # Test resource loading
        css = await plugin_manager.load_resource(
            "discosui",
            "styles.css"
        )
        assert css is not None
        assert "/* DiscoSui styles */" in css
        
        # Test resource modification
        mod_result = await plugin_manager.update_resource(
            "discosui",
            "styles.css",
            "/* Updated DiscoSui styles */\n" + css
        )
        assert mod_result["success"] is True 
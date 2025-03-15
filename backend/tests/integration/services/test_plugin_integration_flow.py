"""Integration tests for plugin integration flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
import json

from src.core.config import Settings
from src.services.plugin.plugin_manager import PluginManager
from src.services.plugin.plugin_loader import PluginLoader
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_plugins(tmp_path) -> Path:
    """Create test plugin directory with sample plugins."""
    plugins_path = tmp_path / "plugins"
    plugins_path.mkdir()
    
    # Create sample plugin structure
    plugin_files = {
        "test_plugin": {
            "manifest.json": """{
                "id": "test-plugin",
                "name": "Test Plugin",
                "version": "1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "main": "main.py",
                "dependencies": []
            }""",
            "main.py": """from src.core.plugin import Plugin

class TestPlugin(Plugin):
    async def initialize(self):
        self.register_command("test-command", self.test_command)
        
    async def test_command(self, args):
        return {"message": "Test command executed"}
"""
        },
        "data_plugin": {
            "manifest.json": """{
                "id": "data-plugin",
                "name": "Data Processing Plugin",
                "version": "1.0.0",
                "description": "Plugin for data processing",
                "author": "Test Author",
                "main": "main.py",
                "dependencies": ["pandas"]
            }""",
            "main.py": """from src.core.plugin import Plugin

class DataPlugin(Plugin):
    async def initialize(self):
        self.register_hook("process_data", self.process_data)
        
    async def process_data(self, data):
        return {"processed": data}
"""
        }
    }
    
    # Create plugin files
    for plugin_name, files in plugin_files.items():
        plugin_dir = plugins_path / plugin_name
        plugin_dir.mkdir()
        for filename, content in files.items():
            file_path = plugin_dir / filename
            file_path.write_text(content)
    
    return plugins_path

@pytest.fixture
def test_environment(tmp_path, test_plugins):
    """Set up test environment."""
    # Create necessary directories
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    plugin_data_path = tmp_path / "plugin_data"
    plugin_data_path.mkdir()
    
    return {
        "vault_path": vault_path,
        "plugins_path": test_plugins,
        "plugin_data_path": plugin_data_path
    }

@pytest.mark.asyncio
async def test_plugin_discovery(test_environment):
    """Test plugin discovery and validation."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"]),
        PLUGIN_DATA_PATH=str(test_environment["plugin_data_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Discover plugins
    result = await plugin_manager.discover_plugins()
    
    # Verify discovery results
    assert result.success is True
    assert len(result.discovered_plugins) == 2
    assert "test-plugin" in result.discovered_plugins
    assert "data-plugin" in result.discovered_plugins
    
    # Verify plugin metadata
    test_plugin = result.discovered_plugins["test-plugin"]
    assert test_plugin.name == "Test Plugin"
    assert test_plugin.version == "1.0.0"

@pytest.mark.asyncio
async def test_plugin_loading(test_environment):
    """Test plugin loading and initialization."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Load plugins
    result = await plugin_manager.load_plugins()
    
    # Verify loading results
    assert result.success is True
    assert len(result.loaded_plugins) == 2
    assert all(plugin.is_initialized for plugin in result.loaded_plugins.values())
    
    # Verify plugin functionality
    test_plugin = result.loaded_plugins["test-plugin"]
    command_result = await test_plugin.execute_command("test-command")
    assert command_result["message"] == "Test command executed"

@pytest.mark.asyncio
async def test_plugin_dependency_management(test_environment):
    """Test plugin dependency management."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Check dependencies
    result = await plugin_manager.check_dependencies()
    
    # Verify dependency checking
    assert result.success is True
    assert "pandas" in result.required_dependencies
    assert len(result.missing_dependencies) == 0  # Assuming pandas is installed
    
    # Test dependency installation
    install_result = await plugin_manager.install_dependencies()
    assert install_result.success is True

@pytest.mark.asyncio
async def test_plugin_hook_system(test_environment):
    """Test plugin hook system."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Load plugins
    await plugin_manager.load_plugins()
    
    # Test hook execution
    test_data = {"key": "value"}
    result = await plugin_manager.execute_hook("process_data", test_data)
    
    # Verify hook execution
    assert result.success is True
    assert result.responses["data-plugin"]["processed"] == test_data

@pytest.mark.asyncio
async def test_plugin_data_persistence(test_environment):
    """Test plugin data persistence."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"]),
        PLUGIN_DATA_PATH=str(test_environment["plugin_data_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Save plugin data
    test_data = {"setting": "value"}
    save_result = await plugin_manager.save_plugin_data("test-plugin", test_data)
    
    # Verify data persistence
    assert save_result.success is True
    
    # Load plugin data
    load_result = await plugin_manager.load_plugin_data("test-plugin")
    assert load_result.success is True
    assert load_result.data == test_data

@pytest.mark.asyncio
async def test_plugin_error_handling(test_environment):
    """Test plugin error handling."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        PLUGINS_PATH=str(test_environment["plugins_path"])
    )
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize(settings)
    
    # Create invalid plugin
    invalid_plugin_dir = test_environment["plugins_path"] / "invalid_plugin"
    invalid_plugin_dir.mkdir()
    (invalid_plugin_dir / "manifest.json").write_text("invalid json")
    
    # Test error handling during loading
    result = await plugin_manager.load_plugins()
    
    # Verify error handling
    assert result.success is True  # Overall process should succeed
    assert "invalid_plugin" in result.failed_plugins
    assert len(result.error_messages) > 0 
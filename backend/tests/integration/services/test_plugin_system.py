"""Integration tests for the plugin system."""
import pytest
from typing import Dict, Any

@pytest.mark.integration
class TestPluginSystem:
    """Test suite for plugin system integration."""
    
    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self, initialized_services, test_data_generator, validation_helper):
        """Test complete plugin lifecycle from discovery to unloading."""
        plugin_manager = initialized_services["plugin_manager"]
        
        # 1. Plugin Discovery
        discovery_result = await plugin_manager.discover_plugins()
        await validation_helper(discovery_result, 
                              discovered_plugins_count=2,
                              has_errors=False)
        
        # 2. Plugin Loading
        load_result = await plugin_manager.load_plugins()
        await validation_helper(load_result,
                              loaded_plugins_count=2,
                              has_initialization_errors=False)
        
        # 3. Plugin Execution
        test_plugin = load_result.loaded_plugins["test-plugin"]
        execution_result = await test_plugin.execute_command("test-command")
        await validation_helper(execution_result,
                              message="Test command executed")
        
        # 4. Plugin Data Management
        test_data = await test_data_generator("plugin")
        save_result = await plugin_manager.save_plugin_data(
            test_data["name"], 
            {"settings": {"enabled": True}}
        )
        await validation_helper(save_result)
        
        load_data_result = await plugin_manager.load_plugin_data(test_data["name"])
        await validation_helper(load_data_result,
                              data={"settings": {"enabled": True}})
        
        # 5. Plugin Unloading
        unload_result = await plugin_manager.unload_plugin(test_data["name"])
        await validation_helper(unload_result,
                              unloaded=True)
    
    @pytest.mark.asyncio
    async def test_plugin_dependency_management(self, initialized_services, validation_helper):
        """Test plugin dependency management and resolution."""
        plugin_manager = initialized_services["plugin_manager"]
        
        # Check dependencies
        dep_result = await plugin_manager.check_dependencies()
        await validation_helper(dep_result,
                              has_missing_dependencies=False,
                              required_dependencies_count=lambda x: x > 0)
        
        # Install dependencies
        install_result = await plugin_manager.install_dependencies()
        await validation_helper(install_result,
                              failed_installations=0)
    
    @pytest.mark.asyncio
    async def test_plugin_hook_system(self, initialized_services, validation_helper):
        """Test plugin hook system and event handling."""
        plugin_manager = initialized_services["plugin_manager"]
        
        # Register test hook
        test_data = {"key": "value"}
        hook_result = await plugin_manager.execute_hook("process_data", test_data)
        
        await validation_helper(hook_result,
                              hook_executed=True,
                              responses_count=lambda x: x > 0)
        
        # Verify hook response
        assert "data-plugin" in hook_result.responses
        assert hook_result.responses["data-plugin"]["processed"] == test_data
    
    @pytest.mark.asyncio
    async def test_plugin_error_handling(self, initialized_services, validation_helper):
        """Test plugin error handling and recovery."""
        plugin_manager = initialized_services["plugin_manager"]
        
        # Test invalid plugin loading
        invalid_result = await plugin_manager.load_plugin("non-existent")
        await validation_helper(invalid_result,
                              expected_success=False,
                              error_type="PluginNotFoundError")
        
        # Test invalid command execution
        test_result = await plugin_manager.execute_plugin_command(
            "test-plugin",
            "invalid-command"
        )
        await validation_helper(test_result,
                              expected_success=False,
                              error_type="CommandNotFoundError")
        
        # Test plugin recovery
        recovery_result = await plugin_manager.recover_plugin("test-plugin")
        await validation_helper(recovery_result,
                              recovered=True)
    
    @pytest.mark.asyncio
    async def test_plugin_configuration(self, initialized_services, test_data_generator, validation_helper):
        """Test plugin configuration management."""
        plugin_manager = initialized_services["plugin_manager"]
        
        # Generate test config
        test_config = await test_data_generator("config")
        
        # Update plugin config
        config_result = await plugin_manager.update_plugin_config(
            "test-plugin",
            test_config
        )
        await validation_helper(config_result)
        
        # Verify config
        verify_result = await plugin_manager.get_plugin_config("test-plugin")
        await validation_helper(verify_result,
                              config=test_config) 
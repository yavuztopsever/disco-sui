"""Unit tests for core functionality."""
import pytest
from pathlib import Path
from typing import Dict, Any

@pytest.mark.unit
class TestConfig:
    """Test suite for configuration management."""
    
    def test_config_loading(self, mock_context, mock_fs, assertion_helper):
        """Test configuration loading from different sources."""
        from src.core.config import ConfigManager
        
        config_manager = ConfigManager(context=mock_context)
        
        # Test environment variable loading
        with pytest.MonkeyPatch() as mp:
            mp.setenv("DISCOSUI_DEBUG", "true")
            mp.setenv("DISCOSUI_VAULT_PATH", "/custom/vault")
            
            result = config_manager.load_from_env()
            assertion_helper["assert_success"](result)
            assert result["config"]["debug"] is True
            assert result["config"]["vault_path"] == "/custom/vault"
        
        # Test file loading
        mock_fs.read_text.return_value = """
        {
            "app": {
                "name": "DiscoSui",
                "version": "1.0.0"
            }
        }
        """
        
        result = config_manager.load_from_file("/test/config.json")
        assertion_helper["assert_success"](result)
        assert result["config"]["app"]["name"] == "DiscoSui"
    
    def test_config_validation(self, mock_context, assertion_helper):
        """Test configuration validation."""
        from src.core.config import ConfigManager
        
        config_manager = ConfigManager(context=mock_context)
        
        # Test valid config
        valid_config = {
            "app": {
                "name": "DiscoSui",
                "version": "1.0.0",
                "debug": False
            },
            "paths": {
                "vault": "/valid/path",
                "plugins": "/valid/plugins"
            }
        }
        
        result = config_manager.validate(valid_config)
        assertion_helper["assert_validation"](result, True)
        
        # Test invalid config
        invalid_config = {
            "app": {
                "name": "DiscoSui",
                "version": "invalid"
            }
        }
        
        result = config_manager.validate(invalid_config)
        assertion_helper["assert_validation"](result, False)

@pytest.mark.unit
class TestToolManager:
    """Test suite for tool management."""
    
    def test_tool_registration(self, mock_context, mock_tool_base, assertion_helper):
        """Test tool registration and management."""
        from src.core.tools import ToolManager
        
        tool_manager = ToolManager(context=mock_context)
        
        # Register valid tool
        result = tool_manager.register_tool("test_tool", mock_tool_base)
        assertion_helper["assert_success"](result)
        assert "test_tool" in tool_manager.get_tools()
        
        # Test duplicate registration
        result = tool_manager.register_tool("test_tool", mock_tool_base)
        assertion_helper["assert_error"](result, "Tool already registered")
    
    def test_tool_execution(self, mock_context, mock_tool_base, assertion_helper):
        """Test tool execution flow."""
        from src.core.tools import ToolManager
        
        tool_manager = ToolManager(context=mock_context)
        tool_manager.register_tool("test_tool", mock_tool_base)
        
        # Execute valid tool
        result = tool_manager.execute_tool("test_tool", {"param": "value"})
        assertion_helper["assert_success"](result)
        
        # Execute non-existent tool
        result = tool_manager.execute_tool("invalid_tool", {})
        assertion_helper["assert_error"](result, "Tool not found")
    
    def test_tool_validation(self, mock_context, mock_tool_base, assertion_helper):
        """Test tool input validation."""
        from src.core.tools import ToolManager
        
        tool_manager = ToolManager(context=mock_context)
        tool_manager.register_tool("test_tool", mock_tool_base)
        
        # Validate tool input
        result = tool_manager.validate_tool_input("test_tool", {"param": "value"})
        assertion_helper["assert_validation"](result)

@pytest.mark.unit
class TestServiceManager:
    """Test suite for service management."""
    
    def test_service_lifecycle(self, mock_context, mock_service_base, assertion_helper):
        """Test service lifecycle management."""
        from src.core.services import ServiceManager
        
        service_manager = ServiceManager(context=mock_context)
        
        # Register and start service
        service_manager.register_service("test_service", mock_service_base)
        result = service_manager.start_service("test_service")
        assertion_helper["assert_success"](result)
        
        # Stop service
        result = service_manager.stop_service("test_service")
        assertion_helper["assert_success"](result)
    
    def test_service_dependencies(self, mock_context, mock_service_base, assertion_helper):
        """Test service dependency management."""
        from src.core.services import ServiceManager
        
        service_manager = ServiceManager(context=mock_context)
        
        # Setup services with dependencies
        service_a = mock_service_base
        service_b = mock_service_base
        service_b.dependencies = ["service_a"]
        
        service_manager.register_service("service_a", service_a)
        service_manager.register_service("service_b", service_b)
        
        # Start service with dependencies
        result = service_manager.start_service("service_b")
        assertion_helper["assert_success"](result)
        
        # Verify dependency was started
        assert service_manager.is_service_running("service_a")
    
    def test_service_configuration(self, mock_context, mock_service_base, assertion_helper):
        """Test service configuration management."""
        from src.core.services import ServiceManager
        
        service_manager = ServiceManager(context=mock_context)
        service_manager.register_service("test_service", mock_service_base)
        
        # Update service config
        config = {"param": "value"}
        result = service_manager.update_service_config("test_service", config)
        assertion_helper["assert_success"](result)
        
        # Get service config
        result = service_manager.get_service_config("test_service")
        assertion_helper["assert_success"](result)
        assert result["config"] == config 
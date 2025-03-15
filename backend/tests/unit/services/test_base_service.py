import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.base_service import BaseService

class TestService(BaseService):
    """Test implementation of BaseService for testing."""
    def __init__(self, context=None):
        super().__init__(context)
        self.name = "test_service"
        self._running = False
        self._config = {}

    def _start_impl(self):
        self._running = True
        return {"success": True, "started": True}

    def _stop_impl(self):
        self._running = False
        return {"success": True, "stopped": True}

    def _get_status_impl(self):
        return {
            "success": True,
            "status": "running" if self._running else "stopped",
            "uptime": 3600 if self._running else 0
        }

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def test_service(mock_context):
    return TestService(context=mock_context)

def test_base_service_initialization(test_service):
    """Test base service initialization."""
    assert test_service is not None
    assert test_service.context is not None
    assert test_service.name == "test_service"
    assert not test_service._running

def test_start_service(test_service):
    """Test starting the service."""
    result = test_service.start()
    assert result["success"] is True
    assert result["started"] is True
    assert test_service._running is True

def test_stop_service(test_service):
    """Test stopping the service."""
    # First start the service
    test_service.start()
    
    result = test_service.stop()
    assert result["success"] is True
    assert result["stopped"] is True
    assert test_service._running is False

def test_restart_service(test_service):
    """Test restarting the service."""
    # First start the service
    test_service.start()
    
    result = test_service.restart()
    assert result["success"] is True
    assert result["restarted"] is True
    assert test_service._running is True

def test_get_status(test_service):
    """Test getting service status."""
    # Test status when stopped
    result = test_service.get_status()
    assert result["success"] is True
    assert result["status"] == "stopped"
    assert result["uptime"] == 0
    
    # Test status when running
    test_service.start()
    result = test_service.get_status()
    assert result["success"] is True
    assert result["status"] == "running"
    assert result["uptime"] == 3600

def test_get_config(test_service):
    """Test getting service configuration."""
    result = test_service.get_config()
    assert result["success"] is True
    assert "config" in result
    assert isinstance(result["config"], dict)

def test_update_config(test_service):
    """Test updating service configuration."""
    config_update = {
        "max_threads": 4,
        "timeout": 30
    }
    
    result = test_service.update_config(config_update)
    assert result["success"] is True
    assert result["config"] == config_update
    assert test_service._config == config_update

def test_validate_config(test_service):
    """Test configuration validation."""
    valid_config = {
        "max_threads": 4,
        "timeout": 30
    }
    
    result = test_service.validate_config(valid_config)
    assert result["success"] is True
    assert result["valid"] is True

def test_error_handling_start(test_service):
    """Test error handling during service start."""
    with patch.object(test_service, '_start_impl', side_effect=Exception("Start error")):
        result = test_service.start()
        assert result["success"] is False
        assert "error" in result

def test_error_handling_stop(test_service):
    """Test error handling during service stop."""
    with patch.object(test_service, '_stop_impl', side_effect=Exception("Stop error")):
        result = test_service.stop()
        assert result["success"] is False
        assert "error" in result

def test_error_handling_status(test_service):
    """Test error handling during status check."""
    with patch.object(test_service, '_get_status_impl', side_effect=Exception("Status error")):
        result = test_service.get_status()
        assert result["success"] is False
        assert "error" in result

def test_service_dependencies(test_service):
    """Test service dependency management."""
    # Add dependencies
    test_service.add_dependency("service1")
    test_service.add_dependency("service2")
    
    # Check dependencies
    deps = test_service.get_dependencies()
    assert "service1" in deps
    assert "service2" in deps
    
    # Remove dependency
    test_service.remove_dependency("service1")
    deps = test_service.get_dependencies()
    assert "service1" not in deps
    assert "service2" in deps

def test_service_state_transitions(test_service):
    """Test service state transitions."""
    # Initial state
    assert not test_service._running
    
    # Start -> Running
    test_service.start()
    assert test_service._running
    
    # Running -> Stopped
    test_service.stop()
    assert not test_service._running
    
    # Stopped -> Running (restart)
    test_service.restart()
    assert test_service._running

def test_service_config_validation(test_service):
    """Test configuration validation with invalid config."""
    invalid_config = {
        "invalid_key": "invalid_value"
    }
    
    result = test_service.validate_config(invalid_config)
    assert result["success"] is True  # Validation itself succeeded
    assert result["valid"] is True  # Base implementation accepts any config

def test_service_name_validation(test_service):
    """Test service name validation."""
    assert test_service.name == "test_service"
    assert isinstance(test_service.name, str)
    assert len(test_service.name) > 0

def test_context_access(test_service, mock_context):
    """Test context access and usage."""
    assert test_service.context == mock_context
    
    # Test context method access
    mock_context.get_config.return_value = {"test": "value"}
    config = mock_context.get_config()
    assert config["test"] == "value"

def test_service_lifecycle(test_service):
    """Test complete service lifecycle."""
    # Initial state
    assert not test_service._running
    assert test_service.get_status()["status"] == "stopped"
    
    # Start
    start_result = test_service.start()
    assert start_result["success"]
    assert test_service._running
    assert test_service.get_status()["status"] == "running"
    
    # Restart
    restart_result = test_service.restart()
    assert restart_result["success"]
    assert test_service._running
    assert test_service.get_status()["status"] == "running"
    
    # Stop
    stop_result = test_service.stop()
    assert stop_result["success"]
    assert not test_service._running
    assert test_service.get_status()["status"] == "stopped" 
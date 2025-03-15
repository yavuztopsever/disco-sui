import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.service_manager import ServiceManager

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_content_service():
    return MagicMock()

@pytest.fixture
def mock_audio_service():
    return MagicMock()

@pytest.fixture
def mock_email_service():
    return MagicMock()

@pytest.fixture
def mock_storage_service():
    return MagicMock()

@pytest.fixture
def service_manager(mock_context, mock_content_service, mock_audio_service, 
                   mock_email_service, mock_storage_service):
    manager = ServiceManager(context=mock_context)
    manager._services = {
        "content": mock_content_service,
        "audio": mock_audio_service,
        "email": mock_email_service,
        "storage": mock_storage_service
    }
    return manager

def test_service_manager_initialization(service_manager):
    """Test service manager initialization."""
    assert service_manager is not None
    assert service_manager.context is not None
    assert len(service_manager._services) > 0

def test_get_service(service_manager, mock_content_service):
    """Test getting a service."""
    service = service_manager.get_service("content")
    assert service == mock_content_service

def test_get_nonexistent_service(service_manager):
    """Test getting a nonexistent service."""
    result = service_manager.get_service("nonexistent")
    assert result["success"] is False
    assert "error" in result

def test_register_service(service_manager):
    """Test registering a new service."""
    new_service = MagicMock()
    result = service_manager.register_service("new_service", new_service)
    assert result["success"] is True
    assert service_manager.get_service("new_service") == new_service

def test_register_existing_service(service_manager):
    """Test registering an existing service."""
    new_service = MagicMock()
    result = service_manager.register_service("content", new_service)
    assert result["success"] is False
    assert "error" in result

def test_unregister_service(service_manager):
    """Test unregistering a service."""
    result = service_manager.unregister_service("content")
    assert result["success"] is True
    assert "content" not in service_manager._services

def test_unregister_nonexistent_service(service_manager):
    """Test unregistering a nonexistent service."""
    result = service_manager.unregister_service("nonexistent")
    assert result["success"] is False
    assert "error" in result

def test_list_services(service_manager):
    """Test listing all services."""
    result = service_manager.list_services()
    assert result["success"] is True
    assert "services" in result
    assert len(result["services"]) == 4
    assert "content" in result["services"]

def test_start_service(service_manager, mock_content_service):
    """Test starting a service."""
    mock_content_service.start.return_value = {"success": True, "started": True}
    
    result = service_manager.start_service("content")
    assert result["success"] is True
    assert result["started"] is True
    mock_content_service.start.assert_called_once()

def test_stop_service(service_manager, mock_content_service):
    """Test stopping a service."""
    mock_content_service.stop.return_value = {"success": True, "stopped": True}
    
    result = service_manager.stop_service("content")
    assert result["success"] is True
    assert result["stopped"] is True
    mock_content_service.stop.assert_called_once()

def test_restart_service(service_manager, mock_content_service):
    """Test restarting a service."""
    mock_content_service.stop.return_value = {"success": True, "stopped": True}
    mock_content_service.start.return_value = {"success": True, "started": True}
    
    result = service_manager.restart_service("content")
    assert result["success"] is True
    assert result["restarted"] is True
    mock_content_service.stop.assert_called_once()
    mock_content_service.start.assert_called_once()

def test_get_service_status(service_manager, mock_content_service):
    """Test getting service status."""
    mock_content_service.get_status.return_value = {
        "success": True,
        "status": "running",
        "uptime": 3600
    }
    
    result = service_manager.get_service_status("content")
    assert result["success"] is True
    assert result["status"] == "running"
    assert "uptime" in result

def test_start_all_services(service_manager):
    """Test starting all services."""
    for service in service_manager._services.values():
        service.start.return_value = {"success": True, "started": True}
    
    result = service_manager.start_all_services()
    assert result["success"] is True
    assert len(result["results"]) == len(service_manager._services)
    assert all(r["success"] for r in result["results"])

def test_stop_all_services(service_manager):
    """Test stopping all services."""
    for service in service_manager._services.values():
        service.stop.return_value = {"success": True, "stopped": True}
    
    result = service_manager.stop_all_services()
    assert result["success"] is True
    assert len(result["results"]) == len(service_manager._services)
    assert all(r["success"] for r in result["results"])

def test_get_all_service_statuses(service_manager):
    """Test getting all service statuses."""
    for service in service_manager._services.values():
        service.get_status.return_value = {
            "success": True,
            "status": "running",
            "uptime": 3600
        }
    
    result = service_manager.get_all_service_statuses()
    assert result["success"] is True
    assert len(result["statuses"]) == len(service_manager._services)
    assert all(s["success"] for s in result["statuses"].values())

def test_validate_service_name(service_manager):
    """Test service name validation."""
    # Test valid name
    result = service_manager.validate_service_name("valid_service")
    assert result["success"] is True
    assert result["valid"] is True
    
    # Test invalid name
    result = service_manager.validate_service_name("invalid@service")
    assert result["success"] is True
    assert result["valid"] is False

def test_error_handling_service_operation(service_manager, mock_content_service):
    """Test error handling during service operation."""
    mock_content_service.start.side_effect = Exception("Service error")
    
    result = service_manager.start_service("content")
    assert result["success"] is False
    assert "error" in result

def test_service_dependency_check(service_manager):
    """Test service dependency checking."""
    result = service_manager.check_service_dependencies("content")
    assert result["success"] is True
    assert "dependencies" in result
    assert isinstance(result["dependencies"], list)

def test_get_service_config(service_manager, mock_content_service):
    """Test getting service configuration."""
    mock_content_service.get_config.return_value = {
        "success": True,
        "config": {
            "max_threads": 4,
            "timeout": 30
        }
    }
    
    result = service_manager.get_service_config("content")
    assert result["success"] is True
    assert "config" in result
    assert "max_threads" in result["config"]

def test_update_service_config(service_manager, mock_content_service):
    """Test updating service configuration."""
    config_update = {
        "max_threads": 8,
        "timeout": 60
    }
    mock_content_service.update_config.return_value = {
        "success": True,
        "config": config_update
    }
    
    result = service_manager.update_service_config("content", config_update)
    assert result["success"] is True
    assert result["config"] == config_update 
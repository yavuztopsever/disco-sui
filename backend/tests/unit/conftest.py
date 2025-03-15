"""Shared fixtures for unit tests."""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from typing import Dict, Any

@pytest.fixture
def mock_context():
    """Create a mock context with common attributes."""
    context = MagicMock()
    context.config = {
        "app": {
            "name": "DiscoSui",
            "version": "1.0.0",
            "debug": False
        },
        "paths": {
            "vault": "/test/vault",
            "plugins": "/test/plugins",
            "config": "/test/config"
        }
    }
    return context

@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = MagicMock()
    storage.read.return_value = {"success": True, "data": {}}
    storage.write.return_value = {"success": True}
    storage.exists.return_value = {"success": True, "exists": True}
    storage.delete.return_value = {"success": True}
    return storage

@pytest.fixture
def mock_processor():
    """Create a mock content processor."""
    processor = MagicMock()
    processor.process_markdown.return_value = {
        "success": True,
        "html": "<div>Test content</div>"
    }
    processor.process_metadata.return_value = {
        "success": True,
        "metadata": {"title": "Test", "tags": []}
    }
    return processor

@pytest.fixture
def mock_service_base():
    """Create a mock service base with common methods."""
    service = MagicMock()
    service.start.return_value = {"success": True, "started": True}
    service.stop.return_value = {"success": True, "stopped": True}
    service.get_config.return_value = {"success": True, "config": {}}
    service.validate_config.return_value = {"success": True, "valid": True}
    return service

@pytest.fixture
def mock_tool_base():
    """Create a mock tool base with common methods."""
    tool = MagicMock()
    tool.execute.return_value = {"success": True, "result": {}}
    tool.validate.return_value = {"success": True, "valid": True}
    tool.get_documentation.return_value = {"success": True, "documentation": ""}
    return tool

@pytest.fixture
def test_data_generator():
    """Generate test data for unit tests."""
    
    def generate_test_data(data_type: str, **kwargs) -> Dict[str, Any]:
        """Generate specific test data based on type."""
        if data_type == "note":
            return {
                "title": kwargs.get("title", "Test Note"),
                "content": kwargs.get("content", "Test content"),
                "metadata": kwargs.get("metadata", {"tags": []})
            }
        elif data_type == "email":
            return {
                "subject": kwargs.get("subject", "Test Email"),
                "body": kwargs.get("body", "Test body"),
                "from": kwargs.get("from", "test@example.com"),
                "to": kwargs.get("to", ["recipient@example.com"])
            }
        elif data_type == "audio":
            return {
                "filename": kwargs.get("filename", "test.mp3"),
                "duration": kwargs.get("duration", 60),
                "format": kwargs.get("format", "mp3")
            }
        # Add more data types as needed
        return {}
    
    return generate_test_data

@pytest.fixture
def mock_fs():
    """Create a mock file system."""
    with patch("pathlib.Path") as mock_path:
        # Configure common path operations
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.open = MagicMock()
        yield mock_path

@pytest.fixture
def assertion_helper():
    """Helper functions for common test assertions."""
    
    def assert_success_response(response: Dict[str, Any], 
                              expected_data: Dict[str, Any] = None):
        """Assert successful response format."""
        assert response["success"] is True
        if expected_data:
            for key, value in expected_data.items():
                assert response[key] == value
    
    def assert_error_response(response: Dict[str, Any],
                            expected_error: str = None):
        """Assert error response format."""
        assert response["success"] is False
        assert "error" in response
        if expected_error:
            assert response["error"] == expected_error
    
    def assert_validation_response(response: Dict[str, Any],
                                 expected_valid: bool = True):
        """Assert validation response format."""
        assert response["success"] is True
        assert response["valid"] is expected_valid
        if not expected_valid:
            assert "errors" in response
    
    return {
        "assert_success": assert_success_response,
        "assert_error": assert_error_response,
        "assert_validation": assert_validation_response
    } 
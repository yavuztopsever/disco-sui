"""End-to-end tests for service tools functionality."""

import pytest
import os
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

from src.tools.service_tools import ServiceTools, ServiceManagerTool, ServiceRegistryTool
from src.core.exceptions import ServiceError, ValidationError, ToolError
from src.services.service_manager import service_registry, ServiceStatus

@pytest.fixture
async def service_tools() -> ServiceTools:
    """Create a ServiceTools instance."""
    return ServiceTools()

@pytest.fixture
async def service_manager_tool() -> ServiceManagerTool:
    """Create a ServiceManagerTool instance."""
    return ServiceManagerTool()

@pytest.fixture
async def service_registry_tool() -> ServiceRegistryTool:
    """Create a ServiceRegistryTool instance."""
    return ServiceRegistryTool()

@pytest.mark.asyncio
class TestServiceTools:
    """Test suite for service tools functionality."""
    
    async def test_service_tools_initialization(self, service_tools):
        """Test service tools initialization."""
        assert service_tools.name == "service_tools"
        assert service_tools.description == "Tools for managing and interacting with services"
        assert "list_services" in service_tools.inputs
        assert "start_service" in service_tools.inputs
        assert "stop_service" in service_tools.inputs
    
    async def test_list_services(self, service_tools):
        """Test listing all services."""
        result = await service_tools.execute("list_services")
        assert result["success"] is True
        assert isinstance(result["services"], list)
        assert len(result["services"]) > 0
    
    async def test_service_lifecycle(self, service_tools):
        """Test service lifecycle management."""
        # Start a service
        start_result = await service_tools.execute(
            "start_service",
            service_name="tag_manager"
        )
        assert start_result["success"] is True
        assert start_result["status"] == ServiceStatus.RUNNING.value
        
        # Get service status
        status_result = await service_tools.execute(
            "get_service_status",
            service_name="tag_manager"
        )
        assert status_result["success"] is True
        assert status_result["status"] == ServiceStatus.RUNNING.value
        
        # Stop the service
        stop_result = await service_tools.execute(
            "stop_service",
            service_name="tag_manager"
        )
        assert stop_result["success"] is True
        assert stop_result["status"] == ServiceStatus.STOPPED.value
    
    async def test_service_health_check(self, service_tools):
        """Test service health checking."""
        # Start a service
        await service_tools.execute(
            "start_service",
            service_name="tag_manager"
        )
        
        # Check service health
        health_result = await service_tools.execute(
            "health_check",
            service_name="tag_manager"
        )
        assert health_result["success"] is True
        assert health_result["healthy"] is True
    
    async def test_service_update_trigger(self, service_tools):
        """Test triggering service updates."""
        # Trigger a service update
        update_result = await service_tools.execute(
            "trigger_service_update",
            service_name="tag_manager",
            target_notes=["test_note.md"],
            force_update=True
        )
        assert update_result["success"] is True
        assert "last_run" in update_result
    
    async def test_service_info(self, service_tools):
        """Test retrieving service information."""
        info_result = await service_tools.execute(
            "get_service_info",
            service_name="tag_manager"
        )
        assert info_result["success"] is True
        assert "version" in info_result
        assert "description" in info_result
        assert "dependencies" in info_result
    
    async def test_service_error_handling(self, service_tools):
        """Test service error handling."""
        # Test non-existent service
        error_result = await service_tools.execute(
            "start_service",
            service_name="non_existent_service"
        )
        assert error_result["success"] is False
        assert "not found" in str(error_result["error"]).lower()
        
        # Test invalid action
        error_result = await service_tools.execute(
            "invalid_action",
            service_name="tag_manager"
        )
        assert error_result["success"] is False
        assert "invalid action" in str(error_result["error"]).lower()
    
    async def test_service_dependencies(self, service_tools):
        """Test service dependency management."""
        # Start a service with dependencies
        start_result = await service_tools.execute(
            "start_service",
            service_name="semantic_analyzer"
        )
        assert start_result["success"] is True
        
        # Verify dependencies are running
        deps_result = await service_tools.execute(
            "get_service_info",
            service_name="semantic_analyzer"
        )
        assert deps_result["success"] is True
        for dep in deps_result["dependencies"]:
            status = await service_tools.execute(
                "get_service_status",
                service_name=dep
            )
            assert status["status"] == ServiceStatus.RUNNING.value
    
    async def test_concurrent_service_operations(self, service_tools):
        """Test handling concurrent service operations."""
        # Create multiple concurrent service operations
        services = ["tag_manager", "indexer", "rag"]
        start_tasks = [
            service_tools.execute("start_service", service_name=service)
            for service in services
        ]
        
        # Run tasks concurrently
        results = await asyncio.gather(*start_tasks)
        
        # Verify all operations succeeded
        assert all(result["success"] for result in results)
        
        # Verify all services are running
        for service in services:
            status = await service_tools.execute(
                "get_service_status",
                service_name=service
            )
            assert status["status"] == ServiceStatus.RUNNING.value
    
    async def test_service_recovery(self, service_tools):
        """Test service recovery after failures."""
        # Simulate a service failure
        with patch("src.services.service_manager.service_registry.get_service") as mock_get:
            mock_get.side_effect = Exception("Simulated failure")
            
            # Attempt to start service
            start_result = await service_tools.execute(
                "start_service",
                service_name="tag_manager"
            )
            assert start_result["success"] is False
        
        # Test service recovery
        recovery_result = await service_tools.execute(
            "start_service",
            service_name="tag_manager"
        )
        assert recovery_result["success"] is True
        assert recovery_result["status"] == ServiceStatus.RUNNING.value
    
    async def test_service_configuration(self, service_tools):
        """Test service configuration management."""
        # Update service configuration
        config = {
            "max_concurrent_tasks": 5,
            "update_interval": 300,
            "log_level": "DEBUG"
        }
        
        config_result = await service_tools.execute(
            "update_service_config",
            service_name="tag_manager",
            config=config
        )
        assert config_result["success"] is True
        
        # Verify configuration
        info_result = await service_tools.execute(
            "get_service_info",
            service_name="tag_manager"
        )
        assert info_result["success"] is True
        assert info_result["config"]["max_concurrent_tasks"] == 5
        assert info_result["config"]["update_interval"] == 300
        assert info_result["config"]["log_level"] == "DEBUG" 
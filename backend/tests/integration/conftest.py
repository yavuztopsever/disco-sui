"""Shared fixtures and utilities for integration tests."""
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from src.core.config import Settings
from src.services.service_manager import ServiceManager, ServiceConfig
from src.services.base_service import BaseService
from src.services.organization.tags.tag_manager import TagManager
from src.services.plugin.plugin_manager import PluginManager
from src.services.config.config_manager import ConfigManager
from src.services.organization.auth_manager import AuthManager
from src.services.storage.backup_manager import BackupManager
from src.services.analysis.metrics_collector import MetricsCollector
from src.services.organization.task_manager import TaskManager

@pytest.fixture
async def base_test_environment(tmp_path) -> Dict[str, Path]:
    """Create base test environment with common directories."""
    env = {
        "vault_path": tmp_path / "test_vault",
        "plugins_path": tmp_path / "test_plugins",
        "plugin_data_path": tmp_path / "test_plugin_data",
        "config_path": tmp_path / "test_config",
        "error_path": tmp_path / "test_errors",
        "backup_path": tmp_path / "test_backups",
        "tag_db_path": tmp_path / "test_tags",
        "task_db_path": tmp_path / "test_tasks",
        "metrics_path": tmp_path / "test_metrics",
        "monitoring_path": tmp_path / "test_monitoring",
        "auth_path": tmp_path / "test_auth",
        "token_path": tmp_path / "test_tokens",
        "index_path": tmp_path / "test_index"
    }
    
    # Create all directories
    for path in env.values():
        path.mkdir(parents=True, exist_ok=True)
        
    return env

@pytest.fixture
async def base_settings(base_test_environment) -> Settings:
    """Create base settings with test paths."""
    return Settings(
        VAULT_PATH=str(base_test_environment["vault_path"]),
        PLUGINS_PATH=str(base_test_environment["plugins_path"]),
        PLUGIN_DATA_PATH=str(base_test_environment["plugin_data_path"]),
        CONFIG_PATH=str(base_test_environment["config_path"]),
        ERROR_PATH=str(base_test_environment["error_path"]),
        BACKUP_PATH=str(base_test_environment["backup_path"]),
        TAG_DB_PATH=str(base_test_environment["tag_db_path"]),
        TASK_DB_PATH=str(base_test_environment["task_db_path"]),
        METRICS_PATH=str(base_test_environment["metrics_path"]),
        MONITORING_PATH=str(base_test_environment["monitoring_path"]),
        AUTH_PATH=str(base_test_environment["auth_path"]),
        TOKEN_PATH=str(base_test_environment["token_path"]),
        INDEX_PATH=str(base_test_environment["index_path"])
    )

@pytest.fixture
async def initialized_services(base_settings):
    """Initialize and return common services."""
    service_config = ServiceConfig(
        max_concurrent_services=10,
        service_timeout=30.0,
        enable_monitoring=True,
        storage_path=Path(base_settings.CONFIG_PATH)
    )
    
    service_manager = ServiceManager(config=service_config)
    
    # Initialize all services
    await service_manager.start_services()
    
    return service_manager.services

@pytest.fixture
async def test_data_generator(base_test_environment):
    """Generate test data for integration tests."""
    
    async def generate_test_data(data_type: str, **kwargs) -> Dict[str, Any]:
        """Generate specific test data based on type."""
        if data_type == "plugin":
            return {
                "name": kwargs.get("name", "test-plugin"),
                "version": kwargs.get("version", "1.0.0"),
                "commands": kwargs.get("commands", ["test-command"])
            }
        elif data_type == "config":
            return {
                "app": {
                    "name": "DiscoSui",
                    "version": "1.0.0",
                    "debug": kwargs.get("debug", False)
                }
            }
        elif data_type == "task":
            return {
                "text": kwargs.get("text", "Test task"),
                "is_completed": kwargs.get("is_completed", False),
                "source_file": kwargs.get("source_file", "test.md")
            }
        # Add more data types as needed
        return {}
    
    return generate_test_data

@pytest.fixture
async def validation_helper():
    """Helper functions for common validation patterns."""
    
    async def validate_result(result, expected_success=True, **kwargs):
        """Validate common result patterns."""
        assert result.success is expected_success
        
        for key, value in kwargs.items():
            assert getattr(result, key) == value
            
    return validate_result 
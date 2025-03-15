"""Integration tests for configuration management flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
import yaml
import json

from src.core.config import Settings
from src.services.config.config_manager import ConfigManager
from src.services.config.validation_service import ConfigValidationService
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_configs(tmp_path) -> Path:
    """Create test configuration files."""
    config_path = tmp_path / "config"
    config_path.mkdir()
    
    # Create various configuration files
    configs = {
        "app_config.yaml": """
app:
  name: DiscoSui
  version: 1.0.0
  environment: test
  debug: true

paths:
  vault: ./vault
  plugins: ./plugins
  cache: ./cache

features:
  semantic_search: true
  auto_tagging: true
  task_tracking: true
""",
        
        "user_preferences.json": """{
            "theme": "dark",
            "font_size": 14,
            "auto_sync": true,
            "notifications": {
                "enabled": true,
                "types": ["task_due", "mentions", "updates"]
            }
        }""",
        
        "plugin_config.yaml": """
plugins:
  - name: semantic_analysis
    enabled: true
    settings:
      model: "default"
      threshold: 0.8
      
  - name: task_manager
    enabled: true
    settings:
      auto_schedule: true
      reminder_interval: 30
""",
        
        "search_config.yaml": """
search:
  engine: "semantic"
  max_results: 50
  include_metadata: true
  
indexing:
  auto_index: true
  index_interval: 3600
  excluded_paths: ["temp", "cache"]
"""
    }
    
    for filename, content in configs.items():
        config_file = config_path / filename
        config_file.write_text(content)
    
    return config_path

@pytest.fixture
def test_environment(tmp_path, test_configs):
    """Set up test environment."""
    # Create necessary directories
    backup_path = tmp_path / "config_backups"
    backup_path.mkdir()
    
    return {
        "config_path": test_configs,
        "backup_path": backup_path
    }

@pytest.mark.asyncio
async def test_config_loading(test_environment):
    """Test configuration loading and parsing."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Load configurations
    result = await config_manager.load_configs()
    
    # Verify config loading
    assert result.success is True
    assert result.loaded_configs > 0
    
    # Verify specific configurations
    app_config = result.configs["app_config"]
    assert app_config["app"]["name"] == "DiscoSui"
    assert app_config["app"]["version"] == "1.0.0"
    
    user_prefs = result.configs["user_preferences"]
    assert user_prefs["theme"] == "dark"
    assert user_prefs["notifications"]["enabled"] is True

@pytest.mark.asyncio
async def test_config_validation(test_environment):
    """Test configuration validation."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    validation_service = ConfigValidationService()
    await validation_service.initialize(settings)
    
    # Validate configurations
    result = await validation_service.validate_all_configs()
    
    # Verify validation results
    assert result.success is True
    assert result.valid_configs > 0
    assert len(result.validation_errors) == 0
    
    # Test invalid config
    invalid_config = {
        "app": {
            "name": "DiscoSui",
            "version": "invalid",
            "debug": "not_boolean"
        }
    }
    
    invalid_result = await validation_service.validate_config(invalid_config)
    assert invalid_result.success is False
    assert len(invalid_result.errors) > 0

@pytest.mark.asyncio
async def test_config_update(test_environment):
    """Test configuration updates."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Update configuration
    updates = {
        "app_config": {
            "app": {
                "debug": False,
                "environment": "production"
            }
        }
    }
    
    result = await config_manager.update_configs(updates)
    
    # Verify update
    assert result.success is True
    assert result.updated_count > 0
    
    # Verify updated values
    updated_config = await config_manager.get_config("app_config")
    assert updated_config["app"]["debug"] is False
    assert updated_config["app"]["environment"] == "production"

@pytest.mark.asyncio
async def test_config_backup_restore(test_environment):
    """Test configuration backup and restore functionality."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"]),
        BACKUP_PATH=str(test_environment["backup_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Create backup
    backup_result = await config_manager.create_backup()
    
    # Verify backup creation
    assert backup_result.success is True
    assert backup_result.backup_path is not None
    assert Path(backup_result.backup_path).exists()
    
    # Modify configuration
    await config_manager.update_configs({
        "app_config": {
            "app": {
                "name": "Modified"
            }
        }
    })
    
    # Restore from backup
    restore_result = await config_manager.restore_backup(backup_result.backup_path)
    
    # Verify restoration
    assert restore_result.success is True
    restored_config = await config_manager.get_config("app_config")
    assert restored_config["app"]["name"] == "DiscoSui"

@pytest.mark.asyncio
async def test_config_inheritance(test_environment):
    """Test configuration inheritance and overrides."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Create base and override configs
    base_config = {
        "features": {
            "semantic_search": True,
            "auto_tagging": True
        }
    }
    
    override_config = {
        "features": {
            "auto_tagging": False,
            "new_feature": True
        }
    }
    
    # Apply inheritance
    result = await config_manager.apply_inheritance(base_config, override_config)
    
    # Verify inheritance
    assert result.success is True
    assert result.config["features"]["semantic_search"] is True
    assert result.config["features"]["auto_tagging"] is False
    assert result.config["features"]["new_feature"] is True

@pytest.mark.asyncio
async def test_config_schema_management(test_environment):
    """Test configuration schema management."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    validation_service = ConfigValidationService()
    await validation_service.initialize(settings)
    
    # Define new schema
    new_schema = {
        "type": "object",
        "properties": {
            "feature": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "enabled": {"type": "boolean"}
                },
                "required": ["name", "enabled"]
            }
        }
    }
    
    # Register schema
    result = await validation_service.register_schema("feature_config", new_schema)
    
    # Verify schema registration
    assert result.success is True
    
    # Validate against new schema
    valid_config = {
        "feature": {
            "name": "test_feature",
            "enabled": True
        }
    }
    
    validation_result = await validation_service.validate_against_schema(
        "feature_config",
        valid_config
    )
    
    assert validation_result.success is True

@pytest.mark.asyncio
async def test_config_environment_handling(test_environment):
    """Test environment-specific configuration handling."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Test different environments
    environments = ["development", "testing", "production"]
    
    for env in environments:
        result = await config_manager.load_environment_config(env)
        
        # Verify environment-specific config
        assert result.success is True
        assert result.config["app"]["environment"] == env
        
        # Verify environment-specific features
        if env == "development":
            assert result.config["app"]["debug"] is True
        elif env == "production":
            assert result.config["app"]["debug"] is False

@pytest.mark.asyncio
async def test_config_change_notifications(test_environment):
    """Test configuration change notification system."""
    # Initialize services
    settings = Settings(
        CONFIG_PATH=str(test_environment["config_path"])
    )
    
    config_manager = ConfigManager()
    await config_manager.initialize(settings)
    
    # Register change listener
    changes = []
    
    async def config_change_listener(change_event):
        changes.append(change_event)
    
    await config_manager.register_change_listener(config_change_listener)
    
    # Make configuration change
    await config_manager.update_configs({
        "app_config": {
            "app": {
                "debug": False
            }
        }
    })
    
    # Verify notification
    assert len(changes) > 0
    assert changes[0].config_name == "app_config"
    assert "debug" in changes[0].changed_keys 
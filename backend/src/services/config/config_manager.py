"""Configuration manager implementation."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import yaml

from ...core.exceptions import ConfigurationError
from ..base_service import BaseService


class ConfigManager(BaseService):
    """Service for managing application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the config manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        super().__init__()
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the config manager.
        
        Raises:
            ConfigurationError: If initialization fails
        """
        if self._initialized:
            return
        
        if self.config_path:
            await self.load_config()
        
        self._initialized = True
    
    async def load_config(self) -> None:
        """Load configuration from file.
        
        Raises:
            ConfigurationError: If loading fails
        """
        if not self.config_path:
            raise ConfigurationError("No configuration file path specified")
        
        try:
            if self.config_path.suffix == '.json':
                with open(self.config_path) as f:
                    self._config = json.load(f)
            elif self.config_path.suffix in ('.yaml', '.yml'):
                with open(self.config_path) as f:
                    self._config = yaml.safe_load(f)
            else:
                raise ConfigurationError(f"Unsupported config file format: {self.config_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {str(e)}")
    
    async def save_config(self) -> None:
        """Save configuration to file.
        
        Raises:
            ConfigurationError: If saving fails
        """
        if not self.config_path:
            raise ConfigurationError("No configuration file path specified")
        
        try:
            if self.config_path.suffix == '.json':
                with open(self.config_path, 'w') as f:
                    json.dump(self._config, f, indent=2)
            elif self.config_path.suffix in ('.yaml', '.yml'):
                with open(self.config_path, 'w') as f:
                    yaml.safe_dump(self._config, f)
            else:
                raise ConfigurationError(f"Unsupported config file format: {self.config_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
    
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            config: Configuration values to update
        """
        self._config.update(config)
    
    def clear(self) -> None:
        """Clear all configuration values."""
        self._config.clear()
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._config.clear()
        self._initialized = False 
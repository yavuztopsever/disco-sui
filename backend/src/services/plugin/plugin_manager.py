"""Plugin manager implementation."""

from typing import Dict, List, Optional, Type
from pydantic import BaseModel, ConfigDict

from ...core.exceptions import PluginError
from ..base_service import BaseService


class PluginConfig(BaseModel):
    """Configuration for a plugin."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    version: str
    enabled: bool = True
    config: Optional[Dict] = None


class Plugin:
    """Base class for plugins."""
    
    def __init__(self, config: PluginConfig):
        """Initialize the plugin.
        
        Args:
            config: Plugin configuration
        """
        self.config = config
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass


class PluginManager(BaseService):
    """Service for managing plugins."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        super().__init__()
        self.plugins: Dict[str, Plugin] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the plugin manager and all enabled plugins."""
        if self._initialized:
            return
        
        for plugin in self.plugins.values():
            if plugin.config.enabled:
                await plugin.initialize()
        
        self._initialized = True
    
    def register_plugin(self, plugin_class: Type[Plugin], config: PluginConfig) -> None:
        """Register a new plugin.
        
        Args:
            plugin_class: Plugin class to register
            config: Plugin configuration
            
        Raises:
            PluginError: If plugin registration fails
        """
        if config.name in self.plugins:
            raise PluginError(f"Plugin {config.name} is already registered")
        
        try:
            plugin = plugin_class(config)
            self.plugins[config.name] = plugin
        except Exception as e:
            raise PluginError(f"Failed to register plugin {config.name}: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin instance if found, None otherwise
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins.
        
        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())
    
    async def cleanup(self) -> None:
        """Clean up all plugins."""
        for plugin in self.plugins.values():
            await plugin.cleanup() 
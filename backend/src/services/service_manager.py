from typing import List, Optional, Dict, Any, Callable, Awaitable, Type
import logging
from enum import Enum
from datetime import datetime
import asyncio
from src.core.exceptions import (
    ServiceError,
    ConfigurationError,
    ValidationError
)
from pathlib import Path
from .content.processor import ContentProcessor
from .storage.vault_storage import VaultStorage
from ..core.base_interfaces import ServiceInterface
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceConfig(BaseModel):
    """Configuration for service management."""
    max_concurrent_services: int = 10
    service_timeout: float = 30.0
    enable_monitoring: bool = True
    storage_path: Path = Path(".services")

class ServiceStatus(str, Enum):
    """Service status states."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class BaseService:
    """Base class for all services."""
    def __init__(self):
        self.status = ServiceStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.error: Optional[str] = None
    
    async def start(self):
        self.status = ServiceStatus.STARTING
        self.start_time = datetime.now()
        try:
            await self._start_impl()
            self.status = ServiceStatus.RUNNING
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error = str(e)
            raise
    
    async def stop(self):
        self.status = ServiceStatus.STOPPING
        try:
            await self._stop_impl()
            self.status = ServiceStatus.STOPPED
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error = str(e)
            raise
    
    async def _start_impl(self):
        raise NotImplementedError()
    
    async def _stop_impl(self):
        raise NotImplementedError()

class ContentService(BaseService):
    """Handles all content-related operations."""
    def __init__(self):
        super().__init__()
        self.note_handlers = {}
        self.template_handlers = {}
        self.content_processors = {}
    
    async def _start_impl(self):
        # Initialize note handling
        self.note_handlers = {
            "create": self._create_note,
            "update": self._update_note,
            "delete": self._delete_note,
            "move": self._move_note
        }
        
        # Initialize template handling
        self.template_handlers = {
            "apply": self._apply_template,
            "validate": self._validate_template,
            "create": self._create_template
        }
        
        # Initialize content processors
        self.content_processors = {
            "format": self._format_content,
            "validate": self._validate_content,
            "enhance": self._enhance_content
        }
    
    async def _stop_impl(self):
        self.note_handlers.clear()
        self.template_handlers.clear()
        self.content_processors.clear()
    
    async def process_content(self, action: str, content: Dict[str, Any]) -> Dict[str, Any]:
        if action in self.note_handlers:
            return await self.note_handlers[action](content)
        elif action in self.template_handlers:
            return await self.template_handlers[action](content)
        elif action in self.content_processors:
            return await self.content_processors[action](content)
        else:
            raise ServiceError(f"Unknown content action: {action}")

class AnalysisService(BaseService):
    """Handles all analysis operations."""
    def __init__(self):
        super().__init__()
        self.analyzers = {}
        self.processors = {}
    
    async def _start_impl(self):
        # Initialize analyzers
        self.analyzers = {
            "semantic": self._semantic_analysis,
            "structure": self._structure_analysis,
            "relationships": self._relationship_analysis
        }
        
        # Initialize processors
        self.processors = {
            "extract_entities": self._extract_entities,
            "find_patterns": self._find_patterns,
            "generate_insights": self._generate_insights
        }
    
    async def _stop_impl(self):
        self.analyzers.clear()
        self.processors.clear()
    
    async def analyze_content(self, analysis_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        if analysis_type in self.analyzers:
            return await self.analyzers[analysis_type](content)
        elif analysis_type in self.processors:
            return await self.processors[analysis_type](content)
        else:
            raise ServiceError(f"Unknown analysis type: {analysis_type}")

class StorageService(BaseService):
    """Handles all storage operations."""
    def __init__(self):
        super().__init__()
        self.storage_handlers = {}
        self.index_handlers = {}
    
    async def _start_impl(self):
        # Initialize storage handlers
        self.storage_handlers = {
            "store": self._store_content,
            "retrieve": self._retrieve_content,
            "delete": self._delete_content,
            "update": self._update_content
        }
        
        # Initialize index handlers
        self.index_handlers = {
            "index": self._index_content,
            "search": self._search_index,
            "update_index": self._update_index
        }
    
    async def _stop_impl(self):
        self.storage_handlers.clear()
        self.index_handlers.clear()
    
    async def handle_storage(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if action in self.storage_handlers:
            return await self.storage_handlers[action](data)
        elif action in self.index_handlers:
            return await self.index_handlers[action](data)
        else:
            raise ServiceError(f"Unknown storage action: {action}")

class ServiceManager:
    """Manages all services."""
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self.services: Dict[str, BaseService] = {}
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_services)
        self._setup_services()
    
    def _setup_services(self):
        """Initialize core services."""
        self.services = {
            "content": ContentService(),
            "analysis": AnalysisService(),
            "storage": StorageService()
        }
    
    async def start_services(self):
        """Start all services."""
        for service in self.services.values():
            async with self.semaphore:
                await service.start()
    
    async def stop_services(self):
        """Stop all services."""
        for service in self.services.values():
            async with self.semaphore:
                await service.stop()
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get a service by name."""
        return self.services.get(service_name)
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            name: {
                "status": service.status,
                "start_time": service.start_time,
                "error": service.error
            }
            for name, service in self.services.items()
        }
    
    async def handle_request(self, service_name: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a service request."""
        service = self.get_service(service_name)
        if not service:
            raise ServiceError(f"Service not found: {service_name}")
        
        if service.status != ServiceStatus.RUNNING:
            raise ServiceError(f"Service {service_name} is not running")
        
        async with self.semaphore:
            if service_name == "content":
                return await service.process_content(action, data)
            elif service_name == "analysis":
                return await service.analyze_content(action, data)
            elif service_name == "storage":
                return await service.handle_storage(action, data)
            else:
                raise ServiceError(f"Unknown service action: {action}")

class ServiceRegistry:
    """Registry for managing service instances."""
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, BaseService] = {}
        self._config = ServiceConfig()
        self._manager = ServiceManager(self._config)
        
    def register_service(self, name: str, service: BaseService) -> None:
        """Register a service.
        
        Args:
            name: Service name
            service: Service instance
        """
        if name in self._services:
            raise ServiceError(f"Service {name} already registered")
        self._services[name] = service
        
    def unregister_service(self, name: str) -> None:
        """Unregister a service.
        
        Args:
            name: Service name
        """
        if name not in self._services:
            raise ServiceError(f"Service {name} not registered")
        del self._services[name]
        
    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Optional[BaseService]: The service instance if found
        """
        return self._services.get(name)
        
    def list_services(self) -> List[str]:
        """List all registered services.
        
        Returns:
            List[str]: List of service names
        """
        return list(self._services.keys())
        
    async def start_all(self) -> None:
        """Start all registered services."""
        await self._manager.start_services()
        
    async def stop_all(self) -> None:
        """Stop all registered services."""
        await self._manager.stop_services()
        
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all services.
        
        Returns:
            Dict[str, Any]: Service status information
        """
        return await self._manager.get_service_status()
        
    def update_config(self, config: ServiceConfig) -> None:
        """Update service configuration.
        
        Args:
            config: New configuration
        """
        self._config = config
        self._manager = ServiceManager(self._config)

# Global service registry instance
service_registry = ServiceRegistry()

async def trigger_service_update(
    service_name: str,
    target_notes: Optional[List[str]] = None,
    force_update: bool = False,
    options: Optional[dict] = None
) -> None:
    """Trigger a service to update vault contents.
    
    Args:
        service_name: Name of the service to trigger
        target_notes: Optional list of specific notes to update
        force_update: Whether to force update even if no changes detected
        options: Optional service-specific configuration options
        
    Raises:
        ValidationError: If service is not found
        ServiceError: If service execution fails
    """
    try:
        service = await service_registry.get_service(service_name)
        current_status = await service_registry.get_status(service_name)
        
        if current_status == ServiceStatus.RUNNING:
            raise ServiceError(f"Service {service_name} is already running")
            
        logger.info(f"Triggering service {service_name}")
        await service_registry.update_status(service_name, ServiceStatus.RUNNING)
        
        try:
            # Execute service handler
            await service["handler"](
                target_notes=target_notes,
                force_update=force_update,
                options=options or {}
            )
            await service_registry.update_status(service_name, ServiceStatus.COMPLETED)
            logger.info(f"Service {service_name} completed successfully")
            
        except Exception as e:
            await service_registry.update_status(service_name, ServiceStatus.FAILED)
            logger.error(f"Service {service_name} failed: {e}")
            raise ServiceError(f"Service execution failed: {str(e)}")
            
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error triggering service {service_name}: {e}")
        raise ServiceError(f"Error triggering service: {str(e)}") 
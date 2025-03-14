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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Enum for service execution status."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"

class ServiceRegistry:
    """Registry for managing available services and their states."""
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, dict] = {}
        self._service_status: Dict[str, ServiceStatus] = {}
        self._last_run: Dict[str, datetime] = {}
        self._service_tasks: Dict[str, asyncio.Task] = {}
        self._service_dependencies: Dict[str, List[str]] = {}
    
    async def register_service(
        self,
        name: str,
        handler: Callable[..., Awaitable[None]],
        description: str = "",
        dependencies: List[str] = None
    ) -> None:
        """Register a new service with the registry.
        
        Args:
            name: Unique name of the service
            handler: Async callable that implements the service functionality
            description: Optional description of the service
            dependencies: Optional list of service dependencies
            
        Raises:
            ConfigurationError: If service is already registered or dependencies are invalid
        """
        if name in self._services:
            raise ConfigurationError(f"Service {name} already registered")
            
        # Validate dependencies
        dependencies = dependencies or []
        for dep in dependencies:
            if dep not in self._services:
                raise ConfigurationError(f"Dependency {dep} not found for service {name}")
            
        self._services[name] = {
            "handler": handler,
            "description": description
        }
        self._service_status[name] = ServiceStatus.IDLE
        self._service_dependencies[name] = dependencies
        
    async def get_service(self, name: str) -> dict:
        """Get service details by name.
        
        Args:
            name: Name of the service
            
        Returns:
            dict: Service details
            
        Raises:
            ValidationError: If service is not found
        """
        if name not in self._services:
            raise ValidationError(f"Service {name} not found")
        return self._services[name]
        
    async def get_status(self, name: str) -> ServiceStatus:
        """Get current status of a service.
        
        Args:
            name: Name of the service
            
        Returns:
            ServiceStatus: Current service status
            
        Raises:
            ValidationError: If service is not found
        """
        if name not in self._service_status:
            raise ValidationError(f"Service {name} not found")
        return self._service_status[name]
        
    async def update_status(self, name: str, status: ServiceStatus) -> None:
        """Update the status of a service.
        
        Args:
            name: Name of the service
            status: New status
            
        Raises:
            ValidationError: If service is not found
        """
        if name not in self._service_status:
            raise ValidationError(f"Service {name} not found")
        self._service_status[name] = status
        if status == ServiceStatus.COMPLETED:
            self._last_run[name] = datetime.now()
            
    async def get_last_run(self, name: str) -> Optional[datetime]:
        """Get the last successful run time of a service.
        
        Args:
            name: Name of the service
            
        Returns:
            Optional[datetime]: Last run time or None
            
        Raises:
            ValidationError: If service is not found
        """
        if name not in self._services:
            raise ValidationError(f"Service {name} not found")
        return self._last_run.get(name)
        
    async def list_services(self) -> List[dict]:
        """List all registered services and their current status.
        
        Returns:
            List[dict]: List of service details
        """
        return [
            {
                "name": name,
                "description": service["description"],
                "status": self._service_status[name].value,
                "last_run": self._last_run.get(name),
                "dependencies": self._service_dependencies[name]
            }
            for name, service in self._services.items()
        ]

    async def start_service(self, name: str) -> None:
        """Start a service and its dependencies.
        
        Args:
            name: Name of the service
            
        Raises:
            ValidationError: If service is not found
            ServiceError: If service fails to start
        """
        if name not in self._services:
            raise ValidationError(f"Service {name} not found")
            
        # Check if service is already running
        if self._service_status[name] == ServiceStatus.RUNNING:
            return
            
        # Start dependencies first
        for dep in self._service_dependencies[name]:
            await self.start_service(dep)
            
        try:
            await self.update_status(name, ServiceStatus.STARTING)
            service = self._services[name]
            task = asyncio.create_task(service["handler"]())
            self._service_tasks[name] = task
            await self.update_status(name, ServiceStatus.RUNNING)
        except Exception as e:
            await self.update_status(name, ServiceStatus.FAILED)
            raise ServiceError(f"Failed to start service {name}: {str(e)}")

    async def stop_service(self, name: str) -> None:
        """Stop a service.
        
        Args:
            name: Name of the service
            
        Raises:
            ValidationError: If service is not found
            ServiceError: If service fails to stop
        """
        if name not in self._services:
            raise ValidationError(f"Service {name} not found")
            
        if self._service_status[name] != ServiceStatus.RUNNING:
            return
            
        try:
            await self.update_status(name, ServiceStatus.STOPPING)
            if name in self._service_tasks:
                task = self._service_tasks[name]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._service_tasks[name]
            await self.update_status(name, ServiceStatus.IDLE)
        except Exception as e:
            await self.update_status(name, ServiceStatus.FAILED)
            raise ServiceError(f"Failed to stop service {name}: {str(e)}")

    async def health_check(self, name: str) -> bool:
        """Check if a service is healthy.
        
        Args:
            name: Name of the service
            
        Returns:
            bool: True if service is healthy
            
        Raises:
            ValidationError: If service is not found
        """
        if name not in self._services:
            raise ValidationError(f"Service {name} not found")
            
        # Check if service is running
        if self._service_status[name] != ServiceStatus.RUNNING:
            return False
            
        # Check if service task is still alive
        if name in self._service_tasks:
            task = self._service_tasks[name]
            if task.done() or task.cancelled():
                return False
                
        return True

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

class ServiceManager:
    """Manager for all services."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.services: Dict[str, ServiceInterface] = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize all services."""
        # Initialize core services
        await self._init_service(VaultStorage, self.vault_path)
        await self._init_service(ContentProcessor)
        
        self.logger.info("All services initialized")
        
    async def cleanup(self) -> None:
        """Clean up all services."""
        for service in self.services.values():
            try:
                await service.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up {service.name}: {e}")
                
        self.services.clear()
        self.logger.info("All services cleaned up")
        
    async def get_service(self, name: str) -> Optional[ServiceInterface]:
        """Get service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance if found
        """
        return self.services.get(name)
        
    async def _init_service(
        self,
        service_class: Type[ServiceInterface],
        *args,
        **kwargs
    ) -> None:
        """Initialize a service.
        
        Args:
            service_class: Service class to initialize
            *args: Positional arguments for service
            **kwargs: Keyword arguments for service
        """
        try:
            service = service_class(*args, **kwargs)
            await service.initialize()
            self.services[service.name] = service
            self.logger.info(f"Initialized service: {service.name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize {service_class.__name__}: {e}")
            raise 
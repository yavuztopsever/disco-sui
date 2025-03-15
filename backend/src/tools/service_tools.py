from typing import List, Optional, Dict, Any
import logging
from src.core.exceptions import (
    ServiceError,
    ValidationError,
    ToolError
)
from src.core.tool_interfaces import ServiceTool, ServiceRegistry
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManagerTool(ServiceTool):
    """Tool for managing services."""
    
    async def forward(
        self,
        action: str,
        service_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Manage services.
        
        Args:
            action: Action to perform (start, stop, status, health)
            service_name: Name of the service
            **kwargs: Additional action parameters
            
        Returns:
            Action results
        """
        try:
            if action == "start":
                await self._start_service(service_name)
                return {"success": True, "message": f"Service {service_name} started"}
            elif action == "stop":
                await self._stop_service(service_name)
                return {"success": True, "message": f"Service {service_name} stopped"}
            elif action == "status":
                status = await self._get_service_status(service_name)
                return {"success": True, "status": status}
            elif action == "health":
                health = await self._health_check(service_name)
                return {"success": True, "healthy": health}
            elif action == "update":
                target_paths = [Path(p) for p in kwargs.get("target_paths", [])]
                force_update = kwargs.get("force_update", False)
                result = await self._trigger_service_update(
                    service_name,
                    target_paths,
                    force_update,
                    **kwargs
                )
                return {"success": True, "result": result}
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            logger.error(f"Service action failed: {e}")
            return {"success": False, "error": str(e)}

class ServiceRegistryTool(ServiceTool):
    """Tool for managing the service registry."""
    
    async def forward(
        self,
        action: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Manage service registry.
        
        Args:
            action: Action to perform (list, register)
            **kwargs: Additional action parameters
            
        Returns:
            Action results
        """
        try:
            registry = await self._get_service("service_registry")
            if not registry:
                raise ValueError("Service registry not available")
                
            if action == "list":
                services = await registry.list_services()
                return {"success": True, "services": services}
            elif action == "register":
                service_name = kwargs.get("service_name")
                service_class = kwargs.get("service_class")
                dependencies = kwargs.get("dependencies", [])
                
                if not service_name or not service_class:
                    raise ValueError("Service name and class required")
                    
                service = service_class()
                await registry.register_service(service_name, service, dependencies)
                return {
                    "success": True,
                    "message": f"Service {service_name} registered"
                }
            else:
                raise ValueError(f"Invalid action: {action}")
        except Exception as e:
            logger.error(f"Registry action failed: {e}")
            return {"success": False, "error": str(e)}

class ServiceTools(BaseTool):
    """Tools for managing and interacting with services."""
    
    def __init__(self):
        """Initialize the service tools."""
        super().__init__()
        self.name = "service_tools"
        self.description = "Tools for managing and interacting with services"
        
    def get_required_fields(self, action: str) -> List[str]:
        """Get required fields for a specific action.
        
        Args:
            action (str): The action to get required fields for
            
        Returns:
            List[str]: List of required field names
        """
        action_config = self.inputs.get(action, {})
        return action_config.get("required", [])
        
    async def _list_services(self) -> List[dict]:
        """List all registered services and their current status.
        
        Returns:
            List[dict]: List of service details including name, description, status, and last run time
            
        Raises:
            ToolError: If listing services fails
        """
        try:
            return await service_registry.list_services()
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            raise ToolError(f"Failed to list services: {str(e)}")
            
    async def _get_service_status(self, service_name: str) -> str:
        """Get the current status of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            str: Current service status
            
        Raises:
            ValidationError: If service is not found
            ToolError: If getting status fails
        """
        try:
            status = await service_registry.get_status(service_name)
            return status.value
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get status for service {service_name}: {e}")
            raise ToolError(f"Failed to get service status: {str(e)}")
            
    async def _start_service(self, service_name: str) -> None:
        """Start a service and its dependencies.
        
        Args:
            service_name: Name of the service
            
        Raises:
            ValidationError: If service is not found
            ServiceError: If service fails to start
            ToolError: If starting service fails
        """
        try:
            await service_registry.start_service(service_name)
            logger.info(f"Started service {service_name}")
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            raise ToolError(f"Failed to start service: {str(e)}")
            
    async def _stop_service(self, service_name: str) -> None:
        """Stop a service.
        
        Args:
            service_name: Name of the service
            
        Raises:
            ValidationError: If service is not found
            ServiceError: If service fails to stop
            ToolError: If stopping service fails
        """
        try:
            await service_registry.stop_service(service_name)
            logger.info(f"Stopped service {service_name}")
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            raise ToolError(f"Failed to stop service: {str(e)}")
            
    async def _trigger_service_update(
        self,
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
            ToolError: If triggering service fails
        """
        try:
            await service_registry.trigger_service_update(
                service_name,
                target_notes=target_notes,
                force_update=force_update,
                options=options
            )
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to trigger service {service_name}: {e}")
            raise ToolError(f"Failed to trigger service: {str(e)}")
            
    async def _health_check(self, service_name: str) -> bool:
        """Check if a service is healthy.
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if service is healthy
            
        Raises:
            ValidationError: If service is not found
            ToolError: If health check fails
        """
        try:
            return await service_registry.health_check(service_name)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to check health for service {service_name}: {e}")
            raise ToolError(f"Failed to check service health: {str(e)}")
            
    async def _get_service_info(self, service_name: str) -> dict:
        """Get detailed information about a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            dict: Service details including status, last run time, and dependencies
            
        Raises:
            ValidationError: If service is not found
            ToolError: If getting service info fails
        """
        try:
            service = await service_registry.get_service(service_name)
            status = await service_registry.get_status(service_name)
            last_run = await service_registry.get_last_run(service_name)
            
            return {
                "name": service_name,
                "description": service["description"],
                "status": status.value,
                "last_run": last_run,
                "is_healthy": await self.health_check(service_name)
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get info for service {service_name}: {e}")
            raise ToolError(f"Failed to get service info: {str(e)}")

    def get_examples(self) -> List[Dict[str, Any]]:
        """Get example usage of the tool.
        
        Returns:
            List[Dict[str, Any]]: List of example usages
        """
        return [
            {
                "action": "list_services",
                "description": "List all registered services",
                "example": "await service_tools.execute('list_services')"
            },
            {
                "action": "start_service",
                "description": "Start a service",
                "example": "await service_tools.execute('start_service', service_name='tag_manager')"
            },
            {
                "action": "trigger_service_update",
                "description": "Trigger a service update",
                "example": """await service_tools.execute(
    'trigger_service_update',
    service_name='tag_manager',
    target_notes=['note1.md', 'note2.md'],
    force_update=True
)"""
            }
        ]

# Global service tools instance
service_tools = ServiceTools() 
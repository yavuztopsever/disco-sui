from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class BaseService(ABC):
    """Base class for all services in DiscoSui."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the service with optional configuration.
        
        Args:
            config (Optional[Dict[str, Any]]): Service configuration dictionary
        """
        self.config = config or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize service-specific resources and connections."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service and any background tasks."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service and cleanup resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy and operational.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        pass 
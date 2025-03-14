from typing import Dict, Any, Optional, List, Protocol
from pathlib import Path
from abc import ABC, abstractmethod

class BaseInterface(ABC):
    """Base interface for all components."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Component name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Component description."""
        pass

class ServiceInterface(BaseInterface):
    """Base interface for all services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources."""
        pass

class ToolInterface(BaseInterface):
    """Base interface for all tools."""
    
    @abstractmethod
    async def forward(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool's main functionality."""
        pass
    
    @abstractmethod
    async def validate_inputs(self, **kwargs) -> bool:
        """Validate tool inputs."""
        pass

class ContentProcessorInterface(ServiceInterface):
    """Interface for content processing services."""
    
    @abstractmethod
    async def process_content(
        self,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process content with the service."""
        pass

class StorageInterface(ServiceInterface):
    """Interface for storage services."""
    
    @abstractmethod
    async def read(self, path: Path) -> str:
        """Read content from storage."""
        pass
    
    @abstractmethod
    async def write(self, path: Path, content: str) -> None:
        """Write content to storage."""
        pass
    
    @abstractmethod
    async def delete(self, path: Path) -> None:
        """Delete content from storage."""
        pass

class AnalysisInterface(ServiceInterface):
    """Interface for analysis services."""
    
    @abstractmethod
    async def analyze(
        self,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content."""
        pass 
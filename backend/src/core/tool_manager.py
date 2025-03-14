from typing import Dict, List, Optional, Any, Type, Callable
from pydantic import BaseModel, Field
from ..core.exceptions import LLMError, RAGError, ToolError
from ..core.config import settings
from smolagents import LiteLLMModel, Tool, ToolCallingAgent
import os
import logging
from pathlib import Path
from datetime import datetime
import asyncio
from enum import Enum
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class ToolStats:
    """Statistics for tool usage."""
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    error_types: Dict[str, int] = {}
    dependency_failures: Dict[str, int] = {}

class ToolCategory(str, Enum):
    """Categories of tools available."""
    CONTENT = "content"
    ANALYSIS = "analysis"
    ORGANIZATION = "organization"
    SERVICE = "service"
    UTILITY = "utility"

class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]
    required_permissions: List[str] = []
    version: str = "1.0.0"
    author: Optional[str] = None
    dependencies: List[str] = []
    usage_examples: List[Dict[str, Any]] = []
    max_retries: int = 3
    timeout: float = 30.0
    concurrent_limit: Optional[int] = None

class ToolConfig(BaseModel):
    """Configuration for tool management."""
    max_concurrent_tools: int = 10
    default_timeout: float = 30.0
    enable_stats: bool = True
    metadata_storage_path: Path = Path(".tool_metadata")
    stats_storage_path: Path = Path(".tool_stats")
    enable_dependency_injection: bool = True
    enable_tool_composition: bool = True
    max_chain_length: int = 10
    chain_timeout: float = 300.0
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

class ToolDependency:
    """Manages tool dependencies."""
    def __init__(self, tool_name: str, metadata: ToolMetadata):
        self.tool_name = tool_name
        self.metadata = metadata
        self.dependencies: List[str] = metadata.dependencies
        self._resolved = False
        self._resolution_order: List[str] = []
        
    def add_dependency(self, dependency: str):
        """Add a dependency."""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
            self._resolved = False
            
    def remove_dependency(self, dependency: str):
        """Remove a dependency."""
        if dependency in self.dependencies:
            self.dependencies.remove(dependency)
            self._resolved = False
            
    def is_resolved(self) -> bool:
        """Check if dependencies are resolved."""
        return self._resolved
        
    def get_resolution_order(self) -> List[str]:
        """Get dependency resolution order."""
        return self._resolution_order
        
    def resolve(self, available_tools: List[str]) -> bool:
        """Resolve dependencies."""
        if not self.dependencies:
            self._resolved = True
            self._resolution_order = [self.tool_name]
            return True
            
        # Check if all dependencies are available
        missing = [dep for dep in self.dependencies if dep not in available_tools]
        if missing:
            return False
            
        # Topological sort for resolution order
        visited = set()
        temp = set()
        order = []
        
        def visit(tool: str):
            if tool in temp:
                raise ToolError(f"Circular dependency detected: {tool}")
            if tool in visited:
                return
                
            temp.add(tool)
            for dep in self.dependencies:
                visit(dep)
            temp.remove(tool)
            visited.add(tool)
            order.append(tool)
            
        try:
            visit(self.tool_name)
            self._resolution_order = order
            self._resolved = True
            return True
        except Exception as e:
            logger.error(f"Dependency resolution failed: {e}")
            return False

class ToolRegistry:
    """Handles tool registration and dependency management."""
    def __init__(self):
        self._tools: Dict[str, Type[Any]] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._dependencies: Dict[str, ToolDependency] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    def register(
        self,
        tool_class: Type[Any],
        metadata: ToolMetadata
    ) -> None:
        """Register a tool with metadata."""
        name = metadata.name
        self._tools[name] = tool_class
        self._metadata[name] = metadata
        self._dependencies[name] = ToolDependency(name, metadata)
        
        # Resolve dependencies
        self._dependencies[name].resolve(list(self._tools.keys()))
        
    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)
        self._metadata.pop(name, None)
        self._dependencies.pop(name, None)
        
        # Update dependency resolution for affected tools
        for dep in self._dependencies.values():
            if name in dep.dependencies:
                dep.remove_dependency(name)
                dep.resolve(list(self._tools.keys()))
                
    def get_tool(self, name: str) -> Optional[Type[Any]]:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata."""
        return self._metadata.get(name)
        
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[str]:
        """List available tools."""
        if category:
            return [
                name for name, meta in self._metadata.items()
                if meta.category == category
            ]
        return list(self._tools.keys())
        
    def get_dependencies(
        self,
        tool_name: str
    ) -> Optional[ToolDependency]:
        """Get tool dependencies."""
        return self._dependencies.get(tool_name)
        
    async def validate_tool_chain(
        self,
        chain: List[str]
    ) -> bool:
        """Validate a tool chain."""
        if not chain:
            return False
            
        # Check chain length
        if len(chain) > self.config.max_chain_length:
            return False
            
        # Check tool availability
        for tool_name in chain:
            if tool_name not in self._tools:
                return False
                
        # Check dependency resolution
        for i, tool_name in enumerate(chain):
            dep = self._dependencies[tool_name]
            if not dep.is_resolved():
                return False
                
            # Check if dependencies are satisfied by previous tools
            if i > 0:
                prev_tools = chain[:i]
                for required in dep.dependencies:
                    if required not in prev_tools:
                        return False
                        
        return True

class ToolExecutor:
    """Handles tool execution with dependency injection."""
    def __init__(
        self,
        registry: ToolRegistry,
        config: ToolConfig
    ):
        self.registry = registry
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tools)
        self._stats: Dict[str, ToolStats] = {}
        
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with dependency handling."""
        tool_class = self.registry.get_tool(tool_name)
        if not tool_class:
            raise ToolError(f"Tool {tool_name} not found")
            
        metadata = self.registry.get_metadata(tool_name)
        dependency = self.registry.get_dependencies(tool_name)
        
        if not dependency.is_resolved():
            raise ToolError(f"Unresolved dependencies for {tool_name}")
            
        # Execute dependencies first
        dep_results = {}
        for dep_name in dependency.get_resolution_order()[:-1]:
            dep_result = await self.execute(dep_name, parameters)
            dep_results[dep_name] = dep_result
            
        # Inject dependency results
        if self.config.enable_dependency_injection:
            parameters["dependencies"] = dep_results
            
        # Execute tool with retry logic
        return await self._execute_with_retry(
            tool_class,
            parameters,
            metadata
        )
        
    async def execute_chain(
        self,
        chain: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute a chain of tools."""
        if not await self.registry.validate_tool_chain(
            [step["tool"] for step in chain]
        ):
            raise ToolError("Invalid tool chain")
            
        results = []
        for step in chain:
            tool_name = step["tool"]
            parameters = step["parameters"]
            
            # Add previous results to parameters
            if results and self.config.enable_tool_composition:
                parameters["previous_results"] = results
                
            result = await self.execute(tool_name, parameters)
            results.append(result)
            
        return results
        
    async def _execute_with_retry(
        self,
        tool_class: Type[Any],
        parameters: Dict[str, Any],
        metadata: ToolMetadata
    ) -> Dict[str, Any]:
        """Execute a tool with retry logic."""
        start_time = datetime.now()
        retries = 0
        last_error = None
        
        while retries <= metadata.max_retries:
            try:
                async with self._semaphore:
                    tool = tool_class()
                    result = await asyncio.wait_for(
                        tool.execute(parameters),
                        timeout=metadata.timeout
                    )
                    
                # Update stats
                await self._update_stats(
                    metadata.name,
                    True,
                    start_time
                )
                
                return result
                
            except Exception as e:
                last_error = e
                retries += 1
                
                # Update error stats
                await self._update_stats(
                    metadata.name,
                    False,
                    start_time,
                    type(e).__name__
                )
                
                if retries <= metadata.max_retries:
                    delay = self.config.retry_delay * (
                        self.config.retry_backoff ** (retries - 1)
                    )
                    await asyncio.sleep(delay)
                    
        raise ToolError(
            f"Tool {metadata.name} failed after {retries} retries: {last_error}"
        )
        
    async def _update_stats(
        self,
        tool_name: str,
        success: bool,
        start_time: datetime,
        error_type: Optional[str] = None
    ):
        """Update tool statistics."""
        if not self.config.enable_stats:
            return
            
        stats = self._stats.get(tool_name, ToolStats())
        
        # Update counts
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1
            if error_type:
                stats.error_types[error_type] = (
                    stats.error_types.get(error_type, 0) + 1
                )
                
        # Update timing
        execution_time = (datetime.now() - start_time).total_seconds()
        stats.total_execution_time += execution_time
        total_executions = stats.success_count + stats.failure_count
        stats.average_execution_time = (
            stats.total_execution_time / total_executions
        )
        
        stats.last_used = datetime.now()
        self._stats[tool_name] = stats
        
        # Save stats
        if self.config.enable_stats:
            await self._save_stats(tool_name, stats)
            
    async def _save_stats(self, tool_name: str, stats: ToolStats):
        """Save tool statistics."""
        try:
            file_path = (
                self.config.stats_storage_path /
                f"{tool_name}_stats.json"
            )
            with open(file_path, 'w') as f:
                json.dump(stats.__dict__, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save tool stats: {e}")

class ToolManager:
    """Manages tool registration, execution, and optimization."""
    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig()
        self.registry = ToolRegistry()
        self.executor = ToolExecutor(self.registry, self.config)
        
    def register_tool(
        self,
        tool_class: Type[Any],
        metadata: ToolMetadata
    ) -> None:
        """Register a tool."""
        self.registry.register(tool_class, metadata)
        
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool."""
        return await self.executor.execute(tool_name, parameters)
        
    async def execute_chain(
        self,
        chain: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute a tool chain."""
        return await self.executor.execute_chain(chain)
        
    def get_tool_metadata(
        self,
        tool_name: str
    ) -> Optional[ToolMetadata]:
        """Get tool metadata."""
        return self.registry.get_metadata(tool_name)
        
    def get_tool_stats(
        self,
        tool_name: str
    ) -> Optional[ToolStats]:
        """Get tool statistics."""
        return self.executor._stats.get(tool_name)
        
    def get_tool_categories(self) -> List[ToolCategory]:
        """Get available tool categories."""
        return list(set(
            metadata.category
            for metadata in self.registry._metadata.values()
        ))
        
    async def optimize_tool_chain(
        self,
        chain: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimize a tool chain."""
        if not chain:
            return chain
            
        # Validate chain
        if not await self.registry.validate_tool_chain(
            [step["tool"] for step in chain]
        ):
            raise ToolError("Invalid tool chain")
            
        # Group tools by execution time
        fast_tools = []
        slow_tools = []
        
        for step in chain:
            tool_name = step["tool"]
            stats = self.get_tool_stats(tool_name)
            
            if not stats or stats.average_execution_time > 1.0:
                slow_tools.append(step)
            else:
                fast_tools.append(step)
                
        # Optimize chain
        optimized_chain = []
        
        # Add parallel fast tools
        if fast_tools:
            optimized_chain.append({
                "type": "parallel",
                "steps": fast_tools
            })
            
        # Add sequential slow tools
        for tool in slow_tools:
            optimized_chain.append({
                "type": "sequential",
                "step": tool
            })
            
        return optimized_chain
        
    async def cleanup(self):
        """Clean up resources."""
        # Cleanup will be implemented based on specific requirements
        pass 
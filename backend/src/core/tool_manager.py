from typing import Dict, List, Optional, Any, Type, Callable, Union, Awaitable
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

class ToolConfig:
    """Configuration for tool execution."""
    def __init__(
        self,
        max_concurrent_tools: int = 4,
        enable_dependency_injection: bool = True,
        default_timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.max_concurrent_tools = max_concurrent_tools
        self.enable_dependency_injection = enable_dependency_injection
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

class ToolMetadata:
    """Metadata for a tool."""
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        version: str = "1.0.0",
        author: str = "DiscoSui Team",
        documentation: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.author = author
        self.documentation = documentation

class ToolStats:
    """Statistics for tool execution."""
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.average_execution_time = 0.0
        self.last_execution_time = None
        self.error_counts: Dict[str, int] = {}
        
    def update(
        self,
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ) -> None:
        """Update tool statistics."""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error:
                self.error_counts[error] = self.error_counts.get(error, 0) + 1
                
        # Update execution time stats
        self.average_execution_time = (
            (self.average_execution_time * (self.total_calls - 1) + execution_time)
            / self.total_calls
        )
        self.last_execution_time = execution_time

class ToolCategory(str, Enum):
    """Categories of tools available."""
    CONTENT = "content"
    ANALYSIS = "analysis"
    ORGANIZATION = "organization"
    SERVICE = "service"
    UTILITY = "utility"

class ToolDependency:
    """Represents tool dependencies."""
    
    def __init__(self, tool_name: str):
        """Initialize tool dependency.
        
        Args:
            tool_name: Name of the tool
        """
        self.tool_name = tool_name
        self.dependencies: List[str] = []
        self.resolved = False
        
    def add_dependency(self, dependency: str) -> None:
        """Add a dependency.
        
        Args:
            dependency: Name of the dependent tool
        """
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
            
    def is_resolved(self) -> bool:
        """Check if dependencies are resolved.
        
        Returns:
            bool: True if all dependencies are resolved
        """
        return self.resolved
        
    def get_resolution_order(self) -> List[str]:
        """Get dependency resolution order.
        
        Returns:
            List[str]: List of tool names in resolution order
        """
        order = []
        visited = set()
        
        def visit(name: str):
            if name not in visited:
                visited.add(name)
                for dep in self.dependencies:
                    visit(dep)
                order.append(name)
                
        visit(self.tool_name)
        return order

class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Type[Any]] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._dependencies: Dict[str, ToolDependency] = {}
        self._stats: Dict[str, ToolStats] = {}
        self._manifests: Dict[str, Dict[str, Any]] = {}
        
    def register_tool(
        self,
        tool_class: Type[Any],
        metadata: ToolMetadata,
        dependencies: Optional[List[str]] = None,
        manifest: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool.
        
        Args:
            tool_class: Tool class
            metadata: Tool metadata
            dependencies: Optional list of tool dependencies
            manifest: Optional tool manifest with schema and examples
        """
        if metadata.name in self._tools:
            raise ToolError(f"Tool {metadata.name} already registered")
            
        self._tools[metadata.name] = tool_class
        self._metadata[metadata.name] = metadata
        
        # Set up dependencies
        dep = ToolDependency(metadata.name)
        if dependencies:
            for d in dependencies:
                if d not in self._tools:
                    raise ToolError(f"Dependency {d} not found")
                dep.add_dependency(d)
        self._dependencies[metadata.name] = dep
        
        # Store tool manifest
        if manifest:
            self._manifests[metadata.name] = manifest
        else:
            # Create default manifest from tool properties
            self._manifests[metadata.name] = {
                "name": metadata.name,
                "description": metadata.description,
                "params": {},
                "examples": []
            }
        
        # Initialize stats
        self._stats[metadata.name] = ToolStats()
        
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool.
        
        Args:
            name: Tool name
        """
        if name not in self._tools:
            raise ToolError(f"Tool {name} not registered")
            
        del self._tools[name]
        del self._metadata[name]
        del self._dependencies[name]
        del self._stats[name]
        
    def get_tool(self, name: str) -> Optional[Type[Any]]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[Type[Any]]: Tool class if found
        """
        return self._tools.get(name)
        
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[ToolMetadata]: Tool metadata if found
        """
        return self._metadata.get(name)
    
    def get_manifest(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool manifest with schema and examples.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[Dict[str, Any]]: Tool manifest if found
        """
        return self._manifests.get(name)
        
    def get_dependencies(self, name: str) -> Optional[ToolDependency]:
        """Get tool dependencies.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[ToolDependency]: Tool dependencies if found
        """
        return self._dependencies.get(name)
        
    def get_stats(self, name: str) -> Optional[ToolStats]:
        """Get tool statistics.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[ToolStats]: Tool statistics if found
        """
        return self._stats.get(name)
        
    def list_tools(self) -> List[str]:
        """List all registered tools.
        
        Returns:
            List[str]: List of tool names
        """
        return list(self._tools.keys())
        
    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get tools by category.
        
        Args:
            category: Tool category
            
        Returns:
            List[str]: List of tool names in the category
        """
        return [
            name for name, metadata in self._metadata.items()
            if metadata.category == category
        ]
        
    async def validate_tool_chain(self, chain: List[str]) -> bool:
        """Validate a tool chain.
        
        Args:
            chain: List of tool names in execution order
            
        Returns:
            bool: True if chain is valid
        """
        # Check all tools exist
        for name in chain:
            if name not in self._tools:
                return False
                
        # Check dependencies
        for i, name in enumerate(chain):
            deps = self._dependencies[name]
            for dep in deps.dependencies:
                if dep not in chain[:i]:
                    return False
                    
        return True
        
    def update_stats(
        self,
        name: str,
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ) -> None:
        """Update tool statistics.
        
        Args:
            name: Tool name
            success: Whether execution was successful
            execution_time: Execution time in seconds
            error: Optional error message
        """
        if name in self._stats:
            self._stats[name].update(success, execution_time, error)

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
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
            if error_type:
                stats.error_counts[error_type] = stats.error_counts.get(error_type, 0) + 1
                
        # Update timing
        execution_time = (datetime.now() - start_time).total_seconds()
        stats.total_calls += 1
        stats.average_execution_time = (
            (stats.average_execution_time * (stats.total_calls - 1) + execution_time)
            / stats.total_calls
        )
        stats.last_execution_time = execution_time
        
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
        metadata: ToolMetadata,
        manifest: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool with optional manifest."""
        self.registry.register_tool(tool_class, metadata, manifest=manifest)
        
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
    
    def get_tool_manifest(
        self,
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get tool manifest with schema and examples."""
        return self.registry.get_manifest(tool_name)
        
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
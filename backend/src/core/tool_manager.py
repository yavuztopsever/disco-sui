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

logger = logging.getLogger(__name__)

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

class ToolStats(BaseModel):
    """Statistics for tool usage."""
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    error_types: Dict[str, int] = {}

class ToolConfig(BaseModel):
    """Configuration for tool management."""
    max_concurrent_tools: int = 10
    default_timeout: float = 30.0
    enable_stats: bool = True
    metadata_storage_path: Path = Path(".tool_metadata")
    stats_storage_path: Path = Path(".tool_stats")

class ToolRequest(BaseModel):
    """Pydantic model for tool requests."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the tool execution")
    context: Optional[str] = Field(None, description="Additional context for the tool execution")

class ToolResponse(BaseModel):
    """Pydantic model for tool responses."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Optional[Any] = Field(None, description="The result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    response: str = Field(..., description="Natural language response to the user")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the execution")

class ToolManager:
    """Enhanced tool manager with metadata and statistics tracking."""
    
    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig()
        self.tools: Dict[str, Any] = {}
        self.metadata: Dict[str, ToolMetadata] = {}
        self.stats: Dict[str, ToolStats] = {}
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tools)
        self._setup_storage()
        
    def _setup_storage(self):
        """Setup metadata and stats storage."""
        self.config.metadata_storage_path.mkdir(parents=True, exist_ok=True)
        self.config.stats_storage_path.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
        self._load_stats()
        
    def _load_metadata(self):
        """Load tool metadata from storage."""
        try:
            for file_path in self.config.metadata_storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    metadata_data = json.load(f)
                    metadata = ToolMetadata(**metadata_data)
                    self.metadata[metadata.name] = metadata
        except Exception as e:
            logger.error(f"Failed to load tool metadata: {e}")
            
    def _load_stats(self):
        """Load tool statistics from storage."""
        try:
            for file_path in self.config.stats_storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    stats_data = json.load(f)
                    stats = ToolStats(**stats_data)
                    tool_name = file_path.stem
                    self.stats[tool_name] = stats
        except Exception as e:
            logger.error(f"Failed to load tool stats: {e}")
            
    def register_tool(
        self,
        tool_class: Type[Any],
        metadata: ToolMetadata
    ):
        """Register a new tool with metadata."""
        try:
            # Validate tool class
            if not hasattr(tool_class, "execute"):
                raise ValueError(
                    f"Tool class {tool_class.__name__} must have execute method"
                )
                
            # Initialize tool instance
            tool_instance = tool_class()
            
            # Store tool and metadata
            self.tools[metadata.name] = tool_instance
            self.metadata[metadata.name] = metadata
            
            # Initialize stats if needed
            if metadata.name not in self.stats:
                self.stats[metadata.name] = ToolStats()
                
            # Save metadata
            self._save_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Tool registration failed: {e}")
            raise
            
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with statistics tracking."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
            
        async with self.semaphore:
            start_time = datetime.now()
            try:
                # Execute tool
                result = await self.tools[tool_name].execute(**parameters)
                
                # Update stats
                if self.config.enable_stats:
                    await self._update_stats(
                        tool_name,
                        True,
                        start_time
                    )
                    
                return result
                
            except Exception as e:
                # Update error stats
                if self.config.enable_stats:
                    await self._update_stats(
                        tool_name,
                        False,
                        start_time,
                        error_type=type(e).__name__
                    )
                    
                logger.error(f"Tool execution failed: {e}")
                return {"error": str(e)}
                
    async def execute_tool_chain(
        self,
        chain: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute a chain of tools in sequence."""
        results = []
        context = {}
        
        for step in chain:
            try:
                # Extract tool info
                tool_name = step["tool"]
                parameters = step["parameters"]
                
                # Update parameters with context
                parameters = self._prepare_parameters(parameters, context)
                
                # Execute tool
                result = await self.execute_tool(tool_name, parameters)
                results.append(result)
                
                # Update context with result
                if "success" in result:
                    context.update(result)
                    
            except Exception as e:
                logger.error(f"Tool chain execution failed: {e}")
                results.append({"error": str(e)})
                break
                
        return results
        
    def _prepare_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare parameters with context variables."""
        prepared = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("$"):
                # Replace context variables
                context_key = value[1:]
                prepared[key] = context.get(context_key, value)
            else:
                prepared[key] = value
                
        return prepared
        
    async def execute_parallel_tools(
        self,
        tool_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute multiple tools in parallel."""
        tasks = []
        
        for config in tool_configs:
            task = self.execute_tool(
                config["tool"],
                config["parameters"]
            )
            tasks.append(task)
            
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = {}
            for config, result in zip(tool_configs, results):
                if isinstance(result, Exception):
                    processed_results[config["tool"]] = {
                        "error": str(result)
                    }
                else:
                    processed_results[config["tool"]] = result
                    
            return processed_results
            
        except Exception as e:
            logger.error(f"Parallel tool execution failed: {e}")
            return {"error": str(e)}
            
    def get_tool_metadata(
        self,
        tool_name: str
    ) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool."""
        return self.metadata.get(tool_name)
        
    def get_tool_stats(
        self,
        tool_name: str
    ) -> Optional[ToolStats]:
        """Get statistics for a specific tool."""
        return self.stats.get(tool_name)
        
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[str]:
        """List available tools, optionally filtered by category."""
        if category:
            return [
                name for name, metadata in self.metadata.items()
                if metadata.category == category
            ]
        return list(self.tools.keys())
        
    def get_tool_categories(self) -> List[ToolCategory]:
        """Get list of available tool categories."""
        return list(set(
            metadata.category
            for metadata in self.metadata.values()
        ))
        
    async def _update_stats(
        self,
        tool_name: str,
        success: bool,
        start_time: datetime,
        error_type: Optional[str] = None
    ):
        """Update tool statistics."""
        try:
            stats = self.stats[tool_name]
            
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
            
            # Save updated stats
            await self._save_stats(tool_name, stats)
            
        except Exception as e:
            logger.error(f"Stats update failed: {e}")
            
    def _save_metadata(self, metadata: ToolMetadata):
        """Save tool metadata to storage."""
        try:
            file_path = (
                self.config.metadata_storage_path /
                f"{metadata.name}.json"
            )
            with open(file_path, 'w') as f:
                json.dump(metadata.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save tool metadata: {e}")
            
    async def _save_stats(self, tool_name: str, stats: ToolStats):
        """Save tool statistics to storage."""
        try:
            file_path = (
                self.config.stats_storage_path /
                f"{tool_name}.json"
            )
            with open(file_path, 'w') as f:
                json.dump(stats.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save tool stats: {e}")
            
    def validate_tool_dependencies(
        self,
        tool_name: str
    ) -> List[str]:
        """Validate tool dependencies and return missing ones."""
        if tool_name not in self.metadata:
            return []
            
        metadata = self.metadata[tool_name]
        missing = []
        
        for dep in metadata.dependencies:
            if dep not in self.tools:
                missing.append(dep)
                
        return missing
        
    def get_tool_usage_examples(
        self,
        tool_name: str
    ) -> List[Dict[str, Any]]:
        """Get usage examples for a tool."""
        if tool_name not in self.metadata:
            return []
            
        return self.metadata[tool_name].usage_examples
        
    async def cleanup(self):
        """Clean up tool resources."""
        try:
            # Save all metadata and stats
            for metadata in self.metadata.values():
                self._save_metadata(metadata)
                
            for tool_name, stats in self.stats.items():
                await self._save_stats(tool_name, stats)
                
            # Clear runtime data
            self.tools.clear()
            self.metadata.clear()
            self.stats.clear()
            
        except Exception as e:
            logger.error(f"Tool cleanup failed: {e}")
            
    def get_tool_performance_report(
        self,
        tool_name: str
    ) -> Dict[str, Any]:
        """Generate a performance report for a tool."""
        if tool_name not in self.stats:
            return {}
            
        stats = self.stats[tool_name]
        total_executions = stats.success_count + stats.failure_count
        
        return {
            "total_executions": total_executions,
            "success_rate": (
                stats.success_count / total_executions
                if total_executions > 0 else 0.0
            ),
            "average_execution_time": stats.average_execution_time,
            "error_distribution": stats.error_types,
            "last_used": stats.last_used.isoformat() if stats.last_used else None
        }
        
    async def optimize_tool_chain(
        self,
        chain: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimize a tool chain based on performance statistics."""
        optimized_chain = []
        parallel_group = []
        
        for step in chain:
            tool_name = step["tool"]
            stats = self.stats.get(tool_name)
            
            if not stats or stats.average_execution_time > 1.0:
                # Execute long-running tools sequentially
                if parallel_group:
                    optimized_chain.append({
                        "type": "parallel",
                        "steps": parallel_group
                    })
                    parallel_group = []
                optimized_chain.append({
                    "type": "sequential",
                    "step": step
                })
            else:
                # Group fast tools for parallel execution
                parallel_group.append(step)
                
        # Add remaining parallel group if any
        if parallel_group:
            optimized_chain.append({
                "type": "parallel",
                "steps": parallel_group
            })
            
        return optimized_chain

    def should_use_rag(self, request: str) -> bool:
        """Determine if RAG should be used for the request."""
        try:
            prompt = f"""Determine if this request requires retrieval-augmented generation (RAG):
            Request: {request}
            
            RAG should be used if the request:
            1. Requires searching through existing notes
            2. Needs context from multiple notes
            3. Involves answering questions about existing content
            4. Requires analysis of relationships between notes
            
            Respond with 'true' or 'false' only."""
            
            response = self.llm.generate(prompt)
            return response.lower().strip() == "true"
        except Exception as e:
            self.logger.error(f"Failed to determine RAG usage: {str(e)}")
            raise RAGError(f"Failed to determine RAG usage: {str(e)}")

    def should_use_web_search(self, request: str) -> bool:
        """Determine if web search should be used for the request."""
        try:
            prompt = f"""Determine if this request requires web search:
            Request: {request}
            
            Web search should be used if the request:
            1. Requires information not available in the vault
            2. Needs to verify or update external information
            3. Involves current events or real-time data
            4. Requires external references or citations
            
            Respond with 'true' or 'false' only."""
            
            response = self.llm.generate(prompt)
            return response.lower().strip() == "true"
        except Exception as e:
            self.logger.error(f"Failed to determine web search usage: {str(e)}")
            raise ToolError(f"Failed to determine web search usage: {str(e)}")

    async def route_request(self, request: str) -> ToolRequest:
        """Route a natural language request to appropriate tools using LLM."""
        try:
            # Create a prompt that describes available tools and their capabilities
            tools_description = "\n".join([
                f"- {name}: {info['description']}\n  Inputs: {info['inputs']}\n  Output: {info['output_type']}"
                for name, info in self.tools.items()
            ])
            
            prompt = f"""Given the following user request and available tools, determine the most appropriate tool to use and extract relevant parameters.

            User Request: {request}

            Available Tools:
            {tools_description}

            Format your response as JSON with the following structure:
            {{
                "tool_name": "string",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }},
                "context": "string explaining the reasoning"
            }}

            Ensure the parameters match the tool's input requirements."""

            # Get routing decision from LLM
            response = await self.llm.generate(prompt)
            routing_data = response.json()

            # Validate the routing data
            if "tool_name" not in routing_data or "parameters" not in routing_data:
                raise ValueError("Invalid routing data format")

            return ToolRequest(
                tool_name=routing_data["tool_name"],
                parameters=routing_data["parameters"],
                context=routing_data.get("context")
            )
        except Exception as e:
            self.logger.error(f"Failed to route request: {str(e)}")
            raise ToolError(f"Failed to route request: {str(e)}")

    async def execute_tool(self, tool_request: ToolRequest) -> ToolResponse:
        """Execute a tool with the given parameters."""
        try:
            # Get and validate the tool
            tool = self.get_tool(tool_request.tool_name)
            
            # Validate parameters
            self.validate_tool_parameters(tool_request.tool_name, tool_request.parameters)
            
            # Execute the tool with error handling
            try:
                result = await tool.forward(**tool_request.parameters)
            except Exception as e:
                error_handling = tool.error_handling.get(str(e.__class__.__name__), {})
                if error_handling.get("retry", False):
                    # Implement retry logic here
                    max_retries = error_handling.get("max_retries", 3)
                    for attempt in range(max_retries):
                        try:
                            result = await tool.forward(**tool_request.parameters)
                            break
                        except Exception as retry_e:
                            if attempt == max_retries - 1:
                                raise retry_e
                            await asyncio.sleep(error_handling.get("retry_delay", 1))
                else:
                    raise e
            
            # Format the response using LLM
            response_prompt = f"""Based on the tool execution result and context, create a natural response:

            Tool: {tool_request.tool_name}
            Context: {tool_request.context}
            Result: {result}

            Create a conversational response that:
            1. Acknowledges the user's request
            2. Explains what was done
            3. Provides relevant details from the result
            4. Suggests next steps if appropriate
            5. Includes any relevant error messages or warnings

            Response:"""

            response = await self.llm.generate(response_prompt)
            
            return ToolResponse(
                success=True,
                result=result,
                response=response,
                metadata={
                    "tool_name": tool_request.tool_name,
                    "execution_time": datetime.now().isoformat(),
                    "parameters": tool_request.parameters
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to execute tool {tool_request.tool_name}: {str(e)}")
            return ToolResponse(
                success=False,
                error=str(e),
                response="I encountered an error while processing your request. Could you please try again?",
                metadata={
                    "tool_name": tool_request.tool_name,
                    "error_type": e.__class__.__name__,
                    "execution_time": datetime.now().isoformat()
                }
            )

    async def process_request(self, request: str) -> ToolResponse:
        """Process a natural language request."""
        try:
            # Determine if RAG or web search is needed
            if self.should_use_rag(request):
                # Implement RAG processing
                pass
            elif self.should_use_web_search(request):
                # Implement web search processing
                pass

            # Route the request to appropriate tools
            tool_request = await self.route_request(request)
            
            # Execute the tool
            return await self.execute_tool(tool_request)
        except Exception as e:
            self.logger.error(f"Failed to process request: {str(e)}")
            return ToolResponse(
                success=False,
                error=str(e),
                response="I encountered an error while processing your request. Could you please try again?"
            )

    def get_available_tools(self) -> List[str]:
        """Get a list of available tools."""
        return list(self.registered_tools.keys())

    def get_tool_documentation(self, tool_name: str) -> Dict[str, Any]:
        """Get comprehensive documentation for a specific tool."""
        try:
            tool = self.get_tool(tool_name)
            return tool.get_documentation()
        except Exception as e:
            self.logger.error(f"Failed to get documentation for tool {tool_name}: {str(e)}")
            raise ToolError(f"Failed to get documentation for tool {tool_name}: {str(e)}") 
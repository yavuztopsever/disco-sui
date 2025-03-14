from typing import Dict, List, Optional, Any, Type
import asyncio
from pydantic import BaseModel
import logging
from datetime import datetime
from pathlib import Path
from smolagents import Agent, Tool

from .config import Settings, AgentConfig
from .exceptions import AgentError, StrategyError, ContextError
from .tool_manager import ToolManager
from .logging import get_logger
from .memory import MemoryManager, Memory
from .context import ContextManager
from .strategy import StrategyManager, ExecutionStrategy
from .monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)

class AgentResponse(BaseModel):
    """Response from the agent including the action to take and any relevant data."""
    action: str
    data: Dict[str, Any]
    message: Optional[str] = None

class AgentState(BaseModel):
    """Agent's current state and configuration."""
    active_context: Dict[str, Any] = {}
    active_strategy: Optional[str] = None
    last_execution_time: Optional[datetime] = None
    performance_metrics: Dict[str, float] = {}
    error_count: int = 0

class EnhancedSmolAgent(Agent):
    """Enhanced agent implementation using smolagents with sophisticated capabilities."""
    
    def __init__(self, settings: Settings, tool_manager: ToolManager):
        """Initialize the enhanced agent with configuration and tools."""
        super().__init__()
        self.settings = settings
        self.tool_manager = tool_manager
        self.state = AgentState()
        
        # Core components
        self.memory_manager = MemoryManager()
        self.context_manager = ContextManager()
        self.strategy_manager = StrategyManager()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize agent components and monitoring."""
        # Setup monitoring
        self.performance_monitor.register_metric("response_time")
        self.performance_monitor.register_metric("memory_usage")
        self.performance_monitor.register_metric("success_rate")
        
        # Initialize tools from tool manager
        self.tools = self.tool_manager.get_all_tools()
        
    async def process_request(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a user request with enhanced capabilities."""
        start_time = datetime.now()
        
        try:
            # Update monitoring
            self.performance_monitor.start_operation("request_processing")
            
            # Analyze request and build context
            request_context = await self.context_manager.analyze_request(user_input)
            
            # Get relevant tools based on user input
            relevant_tools = self.tool_manager.get_relevant_tools(user_input)
            
            # Determine if RAG is needed
            if self.tool_manager.should_use_rag(user_input):
                rag_context = await self.tool_manager.get_rag_context(user_input)
                request_context.update(rag_context)
            
            # Merge contexts
            full_context = await self.context_manager.merge_contexts(
                request_context,
                context or {},
                await self.memory_manager.get_relevant_context(user_input)
            )
            
            # Get execution strategy
            strategy = await self.strategy_manager.get_strategy(
                user_input,
                full_context
            )
            self.state.active_strategy = strategy.name
            
            # Execute tool chain with strategy
            result = await self._execute_tool_chain(
                user_input,
                relevant_tools,
                full_context,
                strategy
            )
            
            # Update memory
            await self.memory_manager.store_interaction(
                user_input,
                result,
                full_context
            )
            
            # Learn from interaction
            await self._learn_from_interaction(
                user_input,
                result,
                full_context
            )
            
            # Update metrics
            self._update_metrics(start_time, success=True)
            
            return AgentResponse(
                action=result.get("action", "response"),
                data=result.get("data", {}),
                message=result.get("message")
            )
            
        except Exception as e:
            # Handle error and update metrics
            self._update_metrics(start_time, success=False)
            return await self._handle_error(e)
        
        finally:
            self.performance_monitor.end_operation("request_processing")
            
    async def _execute_tool_chain(
        self,
        user_input: str,
        tools: List[Tool],
        context: Dict[str, Any],
        strategy: ExecutionStrategy
    ) -> Dict[str, Any]:
        """Execute a chain of tools based on strategy."""
        current_context = context.copy()
        
        try:
            for step in strategy.steps:
                # Get tools for this step
                step_tools = [t for t in tools if t.name in step.tool_names]
                
                for tool in step_tools:
                    # Execute tool with current context
                    result = await tool.execute(
                        input=user_input,
                        context=current_context
                    )
                    
                    # Update context with tool result
                    if isinstance(result, dict):
                        current_context.update(result)
                    
                    # Check if we need to stop the chain
                    if result.get("final", False):
                        return result
                    
                    # Update metrics for tool execution
                    await self.strategy_manager.update_tool_metrics(
                        tool.name,
                        result
                    )
                    
            return current_context
            
        except Exception as e:
            logger.error(f"Error executing tool chain: {e}")
            raise AgentError(f"Tool chain execution failed: {str(e)}")
            
    async def _learn_from_interaction(
        self,
        user_input: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Learn from the interaction to improve future performance."""
        try:
            # Update strategy performance metrics
            await self.strategy_manager.update_performance(
                self.state.active_strategy,
                result
            )
            
            # Learn context patterns
            await self.context_manager.learn_patterns(
                user_input,
                context,
                result
            )
            
            # Optimize memory retrieval
            await self.memory_manager.optimize_retrieval(
                user_input,
                result
            )
            
            # Update tool manager's relevance model
            await self.tool_manager.update_relevance_model(
                user_input,
                [tool.name for tool in self.tools],
                result
            )
            
        except Exception as e:
            logger.error(f"Learning from interaction failed: {e}")
            
    def _update_metrics(self, start_time: datetime, success: bool):
        """Update agent performance metrics."""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        self.state.last_execution_time = datetime.now()
        self.state.performance_metrics["last_execution_time"] = execution_time
        
        if success:
            self.state.performance_metrics["success_rate"] = (
                self.state.performance_metrics.get("success_rate", 0) * 0.9 + 0.1
            )
        else:
            self.state.performance_metrics["success_rate"] = (
                self.state.performance_metrics.get("success_rate", 0) * 0.9
            )
            self.state.error_count += 1
            
    async def _handle_error(self, error: Exception) -> AgentResponse:
        """Handle errors with sophisticated error recovery."""
        logger.error(f"Error in agent execution: {error}")
        
        try:
            # Get error recovery strategy
            recovery_strategy = await self.strategy_manager.get_recovery_strategy(error)
            
            # Execute recovery if strategy exists
            if recovery_strategy:
                recovery_tools = self.tool_manager.get_tools_for_strategy(recovery_strategy)
                recovery_result = await self._execute_tool_chain(
                    str(error),
                    recovery_tools,
                    {"error": str(error), "error_type": type(error).__name__},
                    recovery_strategy
                )
                
                return AgentResponse(
                    action="error_recovery",
                    data={
                        "error": str(error),
                        "recovery_attempted": True,
                        "recovery_result": recovery_result
                    },
                    message="Error occurred but recovery was attempted"
                )
                
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {recovery_error}")
            
        return AgentResponse(
            action="error",
            data={"error": str(error)},
            message=f"An error occurred: {str(error)}"
        )
        
    async def optimize_performance(self):
        """Optimize agent performance based on metrics."""
        try:
            # Optimize strategy selection
            await self.strategy_manager.optimize_strategies(
                self.state.performance_metrics
            )
            
            # Optimize memory management
            await self.memory_manager.optimize_storage()
            
            # Optimize context handling
            await self.context_manager.optimize_patterns()
            
            # Optimize tool selection
            await self.tool_manager.optimize_tool_selection(
                self.state.performance_metrics
            )
            
            # Clean up resources
            await self._cleanup_resources()
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            
    async def _cleanup_resources(self):
        """Clean up agent resources."""
        try:
            # Clean up memory
            await self.memory_manager.cleanup()
            
            # Clean up context
            await self.context_manager.cleanup()
            
            # Reset state if needed
            if self.state.error_count > self.settings.max_error_threshold:
                self.state = AgentState()
                
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")

    def update_tools(self):
        """Update the available tools from the tool manager."""
        self.tools = self.tool_manager.get_all_tools() 
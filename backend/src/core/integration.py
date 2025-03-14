from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from pathlib import Path
import asyncio
from enum import Enum

from .memory import MemoryManager, MemoryConfig
from .context import ContextManager, ContextConfig
from .strategy import StrategyManager, StrategyConfig
from .tool_manager import ToolManager, ToolConfig

logger = logging.getLogger(__name__)

class IntegrationConfig(BaseModel):
    """Configuration for the integration layer."""
    memory_config: Optional[MemoryConfig] = None
    context_config: Optional[ContextConfig] = None
    strategy_config: Optional[StrategyConfig] = None
    tool_config: Optional[ToolConfig] = None
    enable_optimization: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0

class ExecutionResult(BaseModel):
    """Model for execution results."""
    success: bool
    result: Dict[str, Any]
    context: Dict[str, Any]
    memory_id: Optional[str] = None
    strategy_id: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None

class IntegrationLayer:
    """Integration layer for coordinating system components."""
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        
        # Initialize components
        self.memory_manager = MemoryManager(self.config.memory_config)
        self.context_manager = ContextManager(self.config.context_config)
        self.strategy_manager = StrategyManager(self.config.strategy_config)
        self.tool_manager = ToolManager(self.config.tool_config)
        
    async def process_request(
        self,
        request: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Process a user request through the system."""
        start_time = datetime.now()
        
        try:
            # Build context
            context = await self._build_context(request, additional_context)
            
            # Select strategy
            strategy = await self._select_strategy(context)
            if not strategy:
                return ExecutionResult(
                    success=False,
                    result={},
                    context=context,
                    error="No suitable strategy found"
                )
                
            # Execute strategy
            result = await self._execute_strategy(strategy, context)
            
            # Update memory
            memory_id = await self._update_memory(
                request,
                context,
                result,
                strategy.strategy_id
            )
            
            # Calculate execution time
            execution_time = (
                datetime.now() - start_time
            ).total_seconds()
            
            return ExecutionResult(
                success=True,
                result=result,
                context=context,
                memory_id=memory_id,
                strategy_id=strategy.strategy_id,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return ExecutionResult(
                success=False,
                result={},
                context={},
                error=str(e)
            )
            
    async def _build_context(
        self,
        request: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context for request processing."""
        try:
            # Get base context from request
            context = await self.context_manager.analyze_request(request)
            
            # Add additional context if provided
            if additional_context:
                context.update(additional_context)
                
            # Get relevant memories
            memories = await self.memory_manager.get_relevant_memories(
                request,
                limit=5
            )
            if memories:
                context["relevant_memories"] = memories
                
            # Add available tools
            context["available_tools"] = self.tool_manager.list_tools()
            
            return context
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return {}
            
    async def _select_strategy(
        self,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """Select appropriate strategy based on context."""
        try:
            # Get available tools
            available_tools = context.get(
                "available_tools",
                self.tool_manager.list_tools()
            )
            
            # Select strategy
            strategy = await self.strategy_manager.select_strategy(
                context,
                available_tools
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"Strategy selection failed: {e}")
            return None
            
    async def _execute_strategy(
        self,
        strategy: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute selected strategy with retry logic."""
        retries = 0
        last_error = None
        
        while retries <= self.config.max_retries:
            try:
                # Create tool executor
                tool_executor = self._create_tool_executor()
                
                # Execute strategy
                result = await self.strategy_manager.execute_strategy(
                    strategy,
                    context,
                    tool_executor
                )
                
                # Check for optimization
                if (
                    self.config.enable_optimization and
                    "chain" in result
                ):
                    result["chain"] = await self.tool_manager.optimize_tool_chain(
                        result["chain"]
                    )
                    
                return result
                
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.config.max_retries:
                    await asyncio.sleep(
                        self.config.retry_delay * (2 ** (retries - 1))
                    )
                    
        logger.error(f"Strategy execution failed after retries: {last_error}")
        return {"error": str(last_error)}
        
    def _create_tool_executor(self) -> Any:
        """Create a tool executor function."""
        async def executor(
            tool_name: str,
            parameters: Dict[str, Any]
        ) -> Dict[str, Any]:
            return await self.tool_manager.execute_tool(
                tool_name,
                parameters
            )
            
        return executor
        
    async def _update_memory(
        self,
        request: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
        strategy_id: str
    ) -> Optional[str]:
        """Update memory with request results."""
        try:
            # Create memory entry
            memory_id = await self.memory_manager.store_interaction(
                user_input=request,
                context=context,
                result=result,
                metadata={
                    "strategy_id": strategy_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Learn from interaction
            await self.context_manager.learn_patterns(
                request,
                context,
                result
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return None
            
    async def optimize_components(self):
        """Optimize all system components."""
        try:
            # Optimize memory
            await self.memory_manager.optimize_retrieval()
            
            # Optimize context patterns
            await self.context_manager.optimize_patterns()
            
            # Optimize strategies
            await self.strategy_manager.optimize_strategies()
            
            logger.info("Successfully optimized all components")
            
        except Exception as e:
            logger.error(f"Component optimization failed: {e}")
            
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components."""
        try:
            memory_stats = await self.memory_manager.get_stats()
            
            return {
                "memory": {
                    "total_memories": memory_stats.get("total_memories", 0),
                    "storage_size": memory_stats.get("storage_size", 0)
                },
                "context": {
                    "total_patterns": len(
                        self.context_manager.patterns
                    )
                },
                "strategies": {
                    "total_strategies": len(
                        self.strategy_manager.strategies
                    ),
                    "active_strategies": len([
                        s for s in self.strategy_manager.strategies.values()
                        if s.success_rate >= self.strategy_manager.config.min_success_rate
                    ])
                },
                "tools": {
                    "total_tools": len(self.tool_manager.tools),
                    "categories": self.tool_manager.get_tool_categories()
                }
            }
            
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")
            return {"error": str(e)}
            
    async def cleanup(self):
        """Clean up all system components."""
        try:
            # Clean up components
            await self.memory_manager.cleanup()
            await self.context_manager.cleanup()
            await self.strategy_manager.cleanup()
            await self.tool_manager.cleanup()
            
            logger.info("Successfully cleaned up all components")
            
        except Exception as e:
            logger.error(f"System cleanup failed: {e}")
            
    def get_component_performance(
        self,
        component_name: str
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific component."""
        try:
            if component_name == "memory":
                return self.memory_manager.get_performance_metrics()
            elif component_name == "tools":
                return {
                    name: self.tool_manager.get_tool_performance_report(name)
                    for name in self.tool_manager.tools
                }
            elif component_name == "strategies":
                return {
                    sid: {
                        "success_rate": s.success_rate,
                        "usage_count": s.usage_count,
                        "last_used": s.last_used
                    }
                    for sid, s in self.strategy_manager.strategies.items()
                }
            else:
                return {"error": f"Unknown component: {component_name}"}
                
        except Exception as e:
            logger.error(f"Performance retrieval failed: {e}")
            return {"error": str(e)}
            
    async def validate_system(self) -> Dict[str, Any]:
        """Validate system components and their integration."""
        validation_results = {
            "memory": {"status": "unknown"},
            "context": {"status": "unknown"},
            "strategies": {"status": "unknown"},
            "tools": {"status": "unknown"},
            "integration": {"status": "unknown"}
        }
        
        try:
            # Validate memory
            memory_stats = await self.memory_manager.get_stats()
            validation_results["memory"] = {
                "status": "ok" if memory_stats else "error",
                "details": memory_stats
            }
            
            # Validate context
            context_patterns = len(self.context_manager.patterns)
            validation_results["context"] = {
                "status": "ok" if context_patterns > 0 else "warning",
                "details": {"total_patterns": context_patterns}
            }
            
            # Validate strategies
            strategies = len(self.strategy_manager.strategies)
            validation_results["strategies"] = {
                "status": "ok" if strategies > 0 else "warning",
                "details": {"total_strategies": strategies}
            }
            
            # Validate tools
            tools = len(self.tool_manager.tools)
            validation_results["tools"] = {
                "status": "ok" if tools > 0 else "error",
                "details": {
                    "total_tools": tools,
                    "categories": self.tool_manager.get_tool_categories()
                }
            }
            
            # Validate integration
            validation_results["integration"] = {
                "status": "ok",
                "details": {
                    "components_ready": all(
                        r["status"] == "ok"
                        for r in validation_results.values()
                        if r["status"] != "unknown"
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"System validation failed: {e}")
            validation_results["error"] = str(e)
            
        return validation_results 
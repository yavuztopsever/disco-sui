from typing import Dict, List, Optional, Any, Type, Union
from pydantic import BaseModel
import logging
from datetime import datetime
import asyncio
from pathlib import Path

from .config import Settings
from .exceptions import AgentError, StrategyError, ContextError
from .tool_manager import ToolManager
from .memory import MemoryManager
from .context import ContextManager
from .strategy import StrategyManager
from .monitoring import PerformanceMonitor
from .integration import (
    IntegrationLayer,
    IntegrationConfig,
    RequestContext,
    RequestType,
    ContextSource
)

logger = logging.getLogger(__name__)

class AgentMetrics(BaseModel):
    """Metrics tracked by the agent."""
    response_time: float = 0.0
    memory_usage: float = 0.0
    success_rate: float = 0.0
    rag_usage: float = 0.0
    tool_usage: float = 0.0
    error_count: int = 0
    request_count: int = 0
    last_update: datetime = datetime.now()

class AgentResponse(BaseModel):
    """Response from the agent including the action to take and any relevant data."""
    success: bool
    action: str
    data: Dict[str, Any]
    message: Optional[str] = None
    context: RequestContext
    execution_time: float = 0.0
    metrics: Optional[AgentMetrics] = None

class AgentState(BaseModel):
    """Agent's current state and configuration."""
    active_context: Optional[RequestContext] = None
    active_strategy: Optional[str] = None
    last_execution_time: Optional[datetime] = None
    metrics: AgentMetrics = AgentMetrics()
    is_processing: bool = False
    last_error: Optional[str] = None

class Agent:
    """Enhanced agent implementation with sophisticated capabilities."""
    
    def __init__(self, settings: Settings):
        """Initialize the agent with configuration."""
        self.settings = settings
        self.state = AgentState()
        
        # Initialize integration layer
        self.integration = IntegrationLayer(
            config=IntegrationConfig(
                memory_config=settings.memory_config,
                context_config=settings.context_config,
                strategy_config=settings.strategy_config,
                tool_config=settings.tool_config
            )
        )
        
        # Initialize performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self._initialize_monitoring()
        
    def _initialize_monitoring(self):
        """Initialize performance monitoring metrics."""
        metrics = [
            "response_time",
            "memory_usage",
            "success_rate",
            "rag_usage",
            "tool_usage",
            "error_rate",
            "request_throughput"
        ]
        for metric in metrics:
            self.performance_monitor.register_metric(metric)
            
    async def process_request(
        self,
        user_input: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a user request with enhanced capabilities."""
        if self.state.is_processing:
            return self._create_busy_response()
            
        self.state.is_processing = True
        start_time = datetime.now()
        
        try:
            # Start monitoring
            self.performance_monitor.start_operation("request_processing")
            
            # Process request through integration layer
            result = await self.integration.process_request(
                user_input,
                additional_context
            )
            
            # Update state
            self._update_state(result)
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, result)
            
            return self._create_success_response(result, execution_time)
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            self.state.error_count += 1
            self.state.last_error = str(e)
            return await self._handle_error(e)
            
        finally:
            self.state.is_processing = False
            self.performance_monitor.end_operation("request_processing")
            
    def _create_busy_response(self) -> AgentResponse:
        """Create response when agent is busy."""
        return AgentResponse(
            success=False,
            action="error",
            data={"error": "Agent is busy"},
            message="Please wait for the current request to complete.",
            context=self.state.active_context or RequestContext(
                request_id="error",
                request_type=RequestType.SYSTEM,
                raw_request="busy"
            ),
            metrics=self.state.metrics
        )
        
    def _create_success_response(
        self,
        result: Any,
        execution_time: float
    ) -> AgentResponse:
        """Create success response."""
        return AgentResponse(
            success=result.success,
            action=result.result.get("action", "response"),
            data=result.result,
            message=result.result.get("message"),
            context=result.context,
            execution_time=execution_time,
            metrics=self.state.metrics
        )
        
    def _update_state(self, result: Any):
        """Update agent state with execution result."""
        self.state.active_context = result.context
        self.state.active_strategy = result.strategy_id
        self.state.last_execution_time = datetime.now()
        
    def _update_metrics(self, execution_time: float, result: Any):
        """Update agent metrics."""
        metrics = self.state.metrics
        
        # Update basic metrics
        metrics.response_time = execution_time
        metrics.request_count += 1
        metrics.last_update = datetime.now()
        
        # Update success rate
        if result.success:
            metrics.success_rate = (
                metrics.success_rate * 0.9 + 0.1
            )
        else:
            metrics.success_rate *= 0.9
            metrics.error_count += 1
            
        # Update RAG and tool usage
        if result.context.contexts.get(ContextSource.RAG):
            metrics.rag_usage += 1
            
        if "tool_usage" in result.result:
            metrics.tool_usage += result.result["tool_usage"]
            
        # Update monitoring metrics
        self._update_monitoring_metrics(metrics)
        
    def _update_monitoring_metrics(self, metrics: AgentMetrics):
        """Update performance monitoring metrics."""
        self.performance_monitor.record_metric(
            "response_time",
            metrics.response_time
        )
        self.performance_monitor.record_metric(
            "success_rate",
            metrics.success_rate
        )
        self.performance_monitor.record_metric(
            "rag_usage",
            metrics.rag_usage / max(metrics.request_count, 1)
        )
        self.performance_monitor.record_metric(
            "tool_usage",
            metrics.tool_usage / max(metrics.request_count, 1)
        )
        self.performance_monitor.record_metric(
            "error_rate",
            metrics.error_count / max(metrics.request_count, 1)
        )
        
    async def _handle_error(self, error: Exception) -> AgentResponse:
        """Handle errors with sophisticated error recovery."""
        try:
            # Get error recovery strategy
            recovery_result = await self.integration.handle_error(error)
            
            if recovery_result.success:
                return AgentResponse(
                    success=True,
                    action="error_recovery",
                    data=recovery_result.result,
                    message="Error occurred but recovery was successful",
                    context=recovery_result.context,
                    metrics=self.state.metrics
                )
                
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {recovery_error}")
            
        return AgentResponse(
            success=False,
            action="error",
            data={"error": str(error)},
            message=f"An error occurred: {str(error)}",
            context=self.state.active_context or RequestContext(
                request_id="error",
                request_type=RequestType.SYSTEM,
                raw_request=str(error)
            ),
            metrics=self.state.metrics
        )
        
    async def optimize_performance(self):
        """Optimize agent performance."""
        try:
            # Optimize through integration layer
            await self.integration.optimize_components()
            
            # Reset state if error count is too high
            if self.state.metrics.error_count > self.settings.max_error_threshold:
                self.state = AgentState()
                
            # Update monitoring
            await self.performance_monitor.analyze_metrics()
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        try:
            # Get system status from integration layer
            system_status = await self.integration.get_system_status()
            
            # Add agent-specific status
            return {
                "agent": {
                    "is_processing": self.state.is_processing,
                    "metrics": self.state.metrics.dict(),
                    "last_execution": self.state.last_execution_time.isoformat()
                    if self.state.last_execution_time else None,
                    "last_error": self.state.last_error
                },
                "system": system_status,
                "monitoring": self.performance_monitor.get_metrics()
            }
            
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")
            return {"error": str(e)}
            
    async def cleanup(self):
        """Clean up agent resources."""
        try:
            # Cleanup through integration layer
            await self.integration.cleanup()
            
            # Reset state
            self.state = AgentState()
            
            # Clear monitoring
            self.performance_monitor.reset()
            
        except Exception as e:
            logger.error(f"Agent cleanup failed: {e}")
            
    async def validate(self) -> Dict[str, Any]:
        """Validate agent and system components."""
        try:
            # Validate through integration layer
            validation_results = await self.integration.validate_system()
            
            # Add agent validation
            validation_results["agent"] = {
                "status": "ok" if self.state.metrics.error_count < self.settings.max_error_threshold else "warning",
                "details": {
                    "metrics": self.state.metrics.dict(),
                    "is_processing": self.state.is_processing,
                    "last_error": self.state.last_error
                }
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 
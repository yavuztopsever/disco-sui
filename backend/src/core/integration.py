from typing import Dict, List, Optional, Any, Type, Union, Tuple, Callable, Awaitable
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from pathlib import Path
import asyncio
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from smolagents import Tool

from .memory import MemoryManager, MemoryConfig
from .context import ContextManager, ContextConfig
from .strategy import StrategyManager, StrategyConfig, Strategy
from .tool_manager import ToolManager, ToolConfig
from .exceptions import AgentError, StrategyError, ContextError

logger = logging.getLogger(__name__)

@dataclass
class IntegrationStats:
    """Statistics for integration operations."""
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 0.0

class RequestType(str, Enum):
    """Types of requests that can be processed."""
    QUERY = "query"  # Information retrieval
    ACTION = "action"  # Task execution
    ANALYSIS = "analysis"  # Content analysis
    ORGANIZATION = "organization"  # Content organization
    SYSTEM = "system"  # System-level operations

class ContextSource(str, Enum):
    """Sources of context information."""
    USER = "user"
    MEMORY = "memory"
    RAG = "rag"
    WEB = "web"
    SYSTEM = "system"

class ContextInfo(BaseModel):
    """Information about a context piece."""
    source: ContextSource
    content: Dict[str, Any]
    relevance: float = 1.0
    timestamp: datetime = datetime.now()

class RequestContext(BaseModel):
    """Enhanced context model for request processing."""
    request_id: str
    request_type: RequestType
    raw_request: str
    contexts: Dict[ContextSource, ContextInfo] = {}
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

    def merge_context(self, source: ContextSource, content: Dict[str, Any], relevance: float = 1.0):
        """Merge new context information."""
        if source in self.contexts:
            # Update existing context
            existing = self.contexts[source]
            if isinstance(content, dict):
                existing.content.update(content)
            else:
                existing.content = content
            existing.relevance = max(existing.relevance, relevance)
            existing.timestamp = datetime.now()
        else:
            # Add new context
            self.contexts[source] = ContextInfo(
                source=source,
                content=content,
                relevance=relevance
            )

    def get_merged_context(self) -> Dict[str, Any]:
        """Get merged context with priority handling."""
        merged = {}
        # Process contexts in order of relevance and recency
        sorted_contexts = sorted(
            self.contexts.values(),
            key=lambda x: (x.relevance, x.timestamp),
            reverse=True
        )
        for context in sorted_contexts:
            if isinstance(context.content, dict):
                for key, value in context.content.items():
                    if key not in merged:
                        merged[key] = value
                    elif isinstance(value, dict) and isinstance(merged[key], dict):
                        merged[key].update(value)
                    elif isinstance(value, list) and isinstance(merged[key], list):
                        merged[key].extend(value)
            else:
                merged[context.source.value] = context.content
        return merged

class IntegrationConfig:
    """Configuration for integration layer."""
    def __init__(
        self,
        max_concurrent_requests: int = 4,
        request_timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_caching: bool = True,
        cache_ttl: int = 3600
    ):
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

class ExecutionResult(BaseModel):
    """Model for execution results."""
    success: bool
    result: Dict[str, Any]
    context: RequestContext
    memory_id: Optional[str] = None
    strategy_id: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None

class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"  # System-level errors
    HIGH = "high"         # Request-level errors
    MEDIUM = "medium"     # Component-level errors
    LOW = "low"          # Recoverable errors
    INFO = "info"        # Informational issues

class ErrorCategory(str, Enum):
    """Categories of errors that can occur."""
    SYSTEM = "system"          # System-level errors
    CONTEXT = "context"        # Context-related errors
    STRATEGY = "strategy"      # Strategy-related errors
    TOOL = "tool"             # Tool execution errors
    MEMORY = "memory"         # Memory-related errors
    RAG = "rag"              # RAG-related errors
    WEB = "web"              # Web search errors
    VALIDATION = "validation" # Validation errors

class ErrorInfo(BaseModel):
    """Detailed information about an error."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Dict[str, Any] = {}
    recovery_attempts: int = 0
    resolved: bool = False
    stack_trace: Optional[str] = None

class RecoveryStrategy(BaseModel):
    """Strategy for error recovery."""
    strategy_id: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    max_attempts: int = 3
    backoff_factor: float = 2.0
    actions: List[Dict[str, Any]] = []
    success_rate: float = 0.0

class ContextPool:
    """Manages a pool of reusable contexts."""
    def __init__(self, max_size: int = 100):
        self.contexts: Dict[str, RequestContext] = {}
        self.max_size = max_size
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[RequestContext]:
        """Get context from pool."""
        async with self._lock:
            return self.contexts.get(key)
            
    async def put(self, key: str, context: RequestContext):
        """Add context to pool."""
        async with self._lock:
            if len(self.contexts) >= self.max_size:
                # Remove oldest context
                oldest = min(self.contexts.values(), key=lambda x: x.timestamp)
                self.contexts.pop(oldest.request_id)
            self.contexts[key] = context
            
    async def cleanup(self):
        """Clean up old contexts."""
        async with self._lock:
            current_time = datetime.now()
            self.contexts = {
                k: v for k, v in self.contexts.items()
                if (current_time - v.timestamp).total_seconds() < 3600  # 1 hour
            }

class ErrorHandler:
    """Unified error handling system."""
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.error_history: List[ErrorInfo] = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_strategies()
        
    def _initialize_strategies(self):
        """Initialize recovery strategies."""
        self.recovery_strategies = {
            ErrorCategory.CONTEXT: RecoveryStrategy(
                strategy_id="context_recovery",
                error_category=ErrorCategory.CONTEXT,
                severity=ErrorSeverity.MEDIUM,
                actions=[
                    {"action": "clear_context", "priority": 1},
                    {"action": "rebuild_context", "priority": 2}
                ]
            ),
            ErrorCategory.TOOL: RecoveryStrategy(
                strategy_id="tool_recovery",
                error_category=ErrorCategory.TOOL,
                severity=ErrorSeverity.HIGH,
                actions=[
                    {"action": "validate_tool", "priority": 1},
                    {"action": "retry_execution", "priority": 2}
                ]
            ),
            ErrorCategory.MEMORY: RecoveryStrategy(
                strategy_id="memory_recovery",
                error_category=ErrorCategory.MEMORY,
                severity=ErrorSeverity.MEDIUM,
                actions=[
                    {"action": "validate_memory", "priority": 1},
                    {"action": "cleanup_memory", "priority": 2}
                ]
            )
        }
        
    async def handle_error(
        self,
        error: Exception,
        context: Optional[RequestContext] = None
    ) -> ExecutionResult:
        """Handle an error with recovery attempts."""
        error_info = self._classify_error(error)
        self.error_history.append(error_info)
        
        # Get recovery strategy
        strategy = self.recovery_strategies.get(error_info.category)
        if not strategy:
            return self._create_error_result(error_info, context)
            
        # Attempt recovery
        for attempt in range(strategy.max_attempts):
            try:
                # Execute recovery actions
                for action in strategy.actions:
                    await self._execute_recovery_action(action, context)
                    
                # Update success rate
                strategy.success_rate = (
                    strategy.success_rate * 0.9 + 0.1  # Weighted update
                )
                
                return ExecutionResult(
                    success=True,
                    result={"recovery": "successful"},
                    context=context or RequestContext(
                        request_id=f"recovery_{error_info.error_id}",
                        request_type=RequestType.SYSTEM,
                        raw_request=str(error)
                    )
                )
                
            except Exception as e:
                logger.error(f"Recovery attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(
                    strategy.backoff_factor ** attempt * self.config.retry_delay
                )
                
        return self._create_error_result(error_info, context)
        
    def _classify_error(self, error: Exception) -> ErrorInfo:
        """Classify an error and create error info."""
        import traceback
        error_id = f"err_{datetime.now().timestamp()}"
        
        # Determine category and severity
        if isinstance(error, AgentError):
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.CRITICAL
        elif isinstance(error, ContextError):
            category = ErrorCategory.CONTEXT
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, StrategyError):
            category = ErrorCategory.STRATEGY
            severity = ErrorSeverity.HIGH
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.HIGH
            
        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            details={"error_type": type(error).__name__},
            stack_trace=traceback.format_exc()
        )
        
    def _create_error_result(
        self,
        error_info: ErrorInfo,
        context: Optional[RequestContext] = None
    ) -> ExecutionResult:
        """Create error execution result."""
        return ExecutionResult(
            success=False,
            result={"error": error_info.message},
            context=context or RequestContext(
                request_id=f"error_{error_info.error_id}",
                request_type=RequestType.SYSTEM,
                raw_request=str(error_info.message)
            ),
            error=error_info.message
        )
        
    async def _execute_recovery_action(
        self,
        action: Dict[str, Any],
        context: Optional[RequestContext]
    ):
        """Execute a recovery action."""
        action_type = action["action"]
        
        if action_type == "clear_context":
            if context:
                context.contexts.clear()
        elif action_type == "rebuild_context":
            if context:
                await self._rebuild_context(context)
        elif action_type == "validate_tool":
            await self._validate_tool(context)
        elif action_type == "retry_execution":
            await self._retry_execution(context)
        else:
            raise ValueError(f"Unknown recovery action: {action_type}")
            
    async def _rebuild_context(self, context: RequestContext):
        """Rebuild context from available sources."""
        # Implementation depends on available context sources
        pass
        
    async def _validate_tool(self, context: Optional[RequestContext]):
        """Validate tool configuration and status."""
        # Implementation depends on tool validation requirements
        pass
        
    async def _retry_execution(self, context: Optional[RequestContext]):
        """Retry failed execution."""
        # Implementation depends on execution requirements
        pass

class IntegrationLayer:
    """Main integration layer with unified error handling and context management."""
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        self.memory_manager = MemoryManager(self.config.memory_config)
        self.context_manager = ContextManager(self.config.context_config)
        self.strategy_manager = StrategyManager(self.config.strategy_config)
        self.tool_manager = ToolManager(self.config.tool_config)
        self.error_handler = ErrorHandler(self.config)
        self.context_pool = ContextPool()
        self.stats = IntegrationStats()
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self._stats_task = asyncio.create_task(self._update_stats())
        
    async def process_request(
        self,
        request: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Process a request with error handling and context management."""
        start_time = datetime.now()
        self.stats.request_count += 1
        
        try:
            # Build context
            context = await self._build_context(request, additional_context)
            
            # Store in context pool
            await self.context_pool.put(context.request_id, context)
            
            # Select and execute strategy
            strategy = await self._select_strategy(context)
            result = await self._execute_strategy(strategy, context)
            
            # Update memory
            memory_id = await self._update_memory(request, context, result)
            
            # Update stats
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats.avg_response_time = (
                self.stats.avg_response_time * 0.9 +
                execution_time * 0.1
            )
            self.stats.success_rate = (
                self.stats.success_rate * 0.9 + 0.1
            )
            
            return ExecutionResult(
                success=True,
                result=result,
                context=context,
                memory_id=memory_id,
                strategy_id=strategy.id if strategy else None,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.stats.error_count += 1
            self.stats.success_rate = (
                self.stats.success_rate * 0.9
            )
            return await self.error_handler.handle_error(e)
            
    async def _build_context(
        self,
        request: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> RequestContext:
        """Build request context from multiple sources."""
        request_type = await self._determine_request_type(request)
        context = RequestContext(
            request_id=f"req_{datetime.now().timestamp()}",
            request_type=request_type,
            raw_request=request
        )
        
        # Add additional context
        if additional_context:
            context.merge_context(ContextSource.USER, additional_context)
            
        # Add context from different sources in parallel
        await asyncio.gather(
            self._add_memory_context(context),
            self._add_rag_context(context),
            self._add_web_context(context),
            self._add_system_context(context)
        )
        
        return context
        
    async def _determine_request_type(self, request: str) -> RequestType:
        """Determine request type based on content."""
        # Implementation depends on request classification logic
        return RequestType.QUERY
        
    async def _add_memory_context(self, context: RequestContext):
        """Add context from memory."""
        try:
            memories = await self.memory_manager.get_relevant_context(
                context.raw_request
            )
            if memories:
                context.merge_context(
                    ContextSource.MEMORY,
                    memories,
                    relevance=0.8
                )
        except Exception as e:
            logger.error(f"Memory context retrieval failed: {e}")
            
    async def _add_rag_context(self, context: RequestContext):
        """Add context from RAG system."""
        if not self.config.enable_rag:
            return
            
        try:
            if await self.tool_manager.should_use_rag(context.raw_request):
                rag_context = await self.tool_manager.get_rag_context(
                    context.raw_request
                )
                if rag_context:
                    context.merge_context(
                        ContextSource.RAG,
                        rag_context,
                        relevance=0.9
                    )
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}")
            
    async def _add_web_context(self, context: RequestContext):
        """Add context from web search."""
        if not self.config.enable_web_search:
            return
            
        try:
            if await self.tool_manager.should_use_web_search(context.raw_request):
                web_results = await self.tool_manager.get_web_search_results(
                    context.raw_request
                )
                if web_results:
                    context.merge_context(
                        ContextSource.WEB,
                        web_results,
                        relevance=0.7
                    )
        except Exception as e:
            logger.error(f"Web context retrieval failed: {e}")
            
    async def _add_system_context(self, context: RequestContext):
        """Add system-level context."""
        try:
            system_context = {
                "available_tools": await self.tool_manager.list_tools(),
                "tool_categories": await self.tool_manager.get_tool_categories(),
                "request_type": context.request_type,
                "timestamp": datetime.now().isoformat()
            }
            context.merge_context(
                ContextSource.SYSTEM,
                system_context,
                relevance=1.0
            )
        except Exception as e:
            logger.error(f"System context retrieval failed: {e}")
            
    async def _select_strategy(self, context: RequestContext) -> Strategy:
        """Select appropriate strategy based on context."""
        return await self.strategy_manager.select_strategy(
            context.get_merged_context()
        )
        
    async def _execute_strategy(
        self,
        strategy: Strategy,
        context: RequestContext
    ) -> Dict[str, Any]:
        """Execute selected strategy with context."""
        return await self.strategy_manager.execute_strategy(
            strategy,
            context.get_merged_context()
        )
        
    async def _update_memory(
        self,
        request: str,
        context: RequestContext,
        result: Dict[str, Any]
    ) -> str:
        """Update memory with request results."""
        return await self.memory_manager.store_interaction(
            request,
            result,
            context.get_merged_context()
        )
        
    async def _periodic_cleanup(self):
        """Periodically clean up resources."""
        while True:
            await asyncio.sleep(self.config.stats_update_interval)
            
            # Check error rate
            error_rate = self.stats.error_count / max(self.stats.request_count, 1)
            if error_rate > self.config.error_threshold:
                logger.warning(f"High error rate detected: {error_rate:.2%}")
                
            # Log performance metrics
            logger.info(
                f"Performance metrics - "
                f"Avg response time: {self.stats.avg_response_time:.2f}s, "
                f"Success rate: {self.stats.success_rate:.2%}"
            )
            
    async def _update_stats(self):
        """Periodically update statistics."""
        while True:
            await asyncio.sleep(self.config.stats_update_interval)
            
            # Check error rate
            error_rate = self.stats.error_count / max(self.stats.request_count, 1)
            if error_rate > self.config.error_threshold:
                logger.warning(f"High error rate detected: {error_rate:.2%}")
                
            # Log performance metrics
            logger.info(
                f"Performance metrics - "
                f"Avg response time: {self.stats.avg_response_time:.2f}s, "
                f"Success rate: {self.stats.success_rate:.2%}"
            )
            
    async def cleanup(self):
        """Clean up all resources."""
        try:
            # Cancel periodic tasks
            self._cleanup_task.cancel()
            self._stats_task.cancel()
            
            # Clean up components
            await self.context_pool.cleanup()
            await self.memory_manager.cleanup()
            await self.strategy_manager.cleanup()
            await self.tool_manager.cleanup()
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

class RequestProcessor:
    """Processes integration requests."""
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
    async def process_request(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an integration request."""
        async with self._semaphore:
            try:
                # Validate request
                self._validate_request(request)
                
                # Process request with retry logic
                result = await self._process_with_retry(request)
                
                return {
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Validate request parameters."""
        required_fields = ["action", "parameters"]
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
                
    async def _process_with_retry(
        self,
        request: Dict[str, Any]
    ) -> Any:
        """Process request with retry logic."""
        retries = 0
        while retries <= self.config.max_retries:
            try:
                return await self._execute_request(request)
            except Exception as e:
                retries += 1
                if retries <= self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** retries))
                else:
                    raise
                    
    async def _execute_request(
        self,
        request: Dict[str, Any]
    ) -> Any:
        """Execute the request."""
        action = request["action"]
        parameters = request["parameters"]
        
        # Execute action
        if action == "process_note":
            return await self._process_note(parameters)
        elif action == "process_folder":
            return await self._process_folder(parameters)
        else:
            raise ValueError(f"Invalid action: {action}")
            
    async def _process_note(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a note."""
        # Implementation specific to note processing
        pass
        
    async def _process_folder(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a folder."""
        # Implementation specific to folder processing
        pass 
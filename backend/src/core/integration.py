from typing import Dict, List, Optional, Any, Type, Union, Tuple
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from pathlib import Path
import asyncio
from enum import Enum

from .memory import MemoryManager, MemoryConfig
from .context import ContextManager, ContextConfig
from .strategy import StrategyManager, StrategyConfig, Strategy
from .tool_manager import ToolManager, ToolConfig
from .exceptions import AgentError, StrategyError, ContextError

logger = logging.getLogger(__name__)

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
        self.contexts[source] = ContextInfo(
            source=source,
            content=content,
            relevance=relevance
        )

    def get_merged_context(self) -> Dict[str, Any]:
        """Get merged context with priority handling."""
        merged = {}
        # Process contexts in order of relevance
        sorted_contexts = sorted(
            self.contexts.values(),
            key=lambda x: x.relevance,
            reverse=True
        )
        for context in sorted_contexts:
            merged.update(context.content)
        return merged

class IntegrationConfig(BaseModel):
    """Configuration for the integration layer."""
    memory_config: Optional[MemoryConfig] = None
    context_config: Optional[ContextConfig] = None
    strategy_config: Optional[StrategyConfig] = None
    tool_config: Optional[ToolConfig] = None
    enable_optimization: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_rag: bool = True
    enable_web_search: bool = True
    context_relevance_threshold: float = 0.5
    max_parallel_contexts: int = 3

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

class RecoveryStrategy(BaseModel):
    """Strategy for error recovery."""
    strategy_id: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    max_attempts: int = 3
    backoff_factor: float = 2.0
    actions: List[Dict[str, Any]] = []
    success_rate: float = 0.0

class IntegrationLayer:
    """Integration layer for coordinating system components."""
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        
        # Initialize components
        self.memory_manager = MemoryManager(self.config.memory_config)
        self.context_manager = ContextManager(self.config.context_config)
        self.strategy_manager = StrategyManager(self.config.strategy_config)
        self.tool_manager = ToolManager(self.config.tool_config)
        
        # Initialize error tracking
        self.errors: Dict[str, ErrorInfo] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self._initialize_recovery_strategies()
        
    def _initialize_recovery_strategies(self):
        """Initialize predefined recovery strategies."""
        # Context recovery strategy
        self.recovery_strategies["context_recovery"] = RecoveryStrategy(
            strategy_id="context_recovery",
            error_category=ErrorCategory.CONTEXT,
            severity=ErrorSeverity.MEDIUM,
            actions=[
                {"action": "clear_context", "params": {}},
                {"action": "rebuild_context", "params": {"use_fallback": True}},
                {"action": "validate_context", "params": {}}
            ]
        )
        
        # Tool execution recovery strategy
        self.recovery_strategies["tool_recovery"] = RecoveryStrategy(
            strategy_id="tool_recovery",
            error_category=ErrorCategory.TOOL,
            severity=ErrorSeverity.HIGH,
            actions=[
                {"action": "validate_tool", "params": {}},
                {"action": "retry_execution", "params": {"use_fallback": True}},
                {"action": "find_alternative_tool", "params": {}}
            ]
        )
        
        # Memory recovery strategy
        self.recovery_strategies["memory_recovery"] = RecoveryStrategy(
            strategy_id="memory_recovery",
            error_category=ErrorCategory.MEMORY,
            severity=ErrorSeverity.MEDIUM,
            actions=[
                {"action": "validate_memory", "params": {}},
                {"action": "cleanup_memory", "params": {}},
                {"action": "rebuild_index", "params": {}}
            ]
        )
        
    async def process_request(
        self,
        request: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Process a user request through the system."""
        start_time = datetime.now()
        
        try:
            # Create request context
            request_context = await self._create_request_context(request)
            
            # Add user-provided context
            if additional_context:
                request_context.merge_context(
                    ContextSource.USER,
                    additional_context
                )
            
            # Build context from all sources in parallel
            await self._build_context_parallel(request_context)
            
            # Select and execute strategy
            strategy = await self._select_strategy(request_context)
            if not strategy:
                return ExecutionResult(
                    success=False,
                    result={},
                    context=request_context,
                    error="No suitable strategy found"
                )
                
            # Execute strategy with retries
            result = await self._execute_with_retries(
                strategy,
                request_context
            )
            
            # Update memory and learn
            memory_id = await self._update_memory_and_learn(
                request,
                request_context,
                result,
                strategy
            )
            
            # Calculate execution time
            execution_time = (
                datetime.now() - start_time
            ).total_seconds()
            
            return ExecutionResult(
                success=True,
                result=result,
                context=request_context,
                memory_id=memory_id,
                strategy_id=strategy.strategy_id,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return ExecutionResult(
                success=False,
                result={},
                context=request_context if 'request_context' in locals() else None,
                error=str(e)
            )
            
    async def _create_request_context(self, request: str) -> RequestContext:
        """Create initial request context."""
        request_type = await self._determine_request_type(request)
        return RequestContext(
            request_id=f"req_{datetime.now().timestamp()}",
            request_type=request_type,
            raw_request=request
        )
        
    async def _determine_request_type(self, request: str) -> RequestType:
        """Determine the type of request."""
        request_lower = request.lower()
        
        if any(q in request_lower for q in ["what", "how", "why", "when", "where", "who", "?"]):
            return RequestType.QUERY
        elif any(a in request_lower for a in ["create", "update", "delete", "move", "rename"]):
            return RequestType.ACTION
        elif any(a in request_lower for a in ["analyze", "compare", "find relationships", "summarize"]):
            return RequestType.ANALYSIS
        elif any(o in request_lower for o in ["organize", "categorize", "tag", "structure"]):
            return RequestType.ORGANIZATION
        else:
            return RequestType.SYSTEM
            
    async def _build_context_parallel(self, request_context: RequestContext):
        """Build context from all sources in parallel."""
        tasks = []
        
        # Create tasks for each context source
        tasks.append(self._get_memory_context(request_context))
        
        if self.config.enable_rag:
            tasks.append(self._get_rag_context(request_context))
            
        if self.config.enable_web_search:
            tasks.append(self._get_web_context(request_context))
            
        # Add system context task
        tasks.append(self._get_system_context(request_context))
        
        # Execute tasks in parallel
        await asyncio.gather(*tasks)
        
    async def _get_memory_context(self, request_context: RequestContext):
        """Get context from memory."""
        try:
            memories = await self.memory_manager.get_relevant_context(
                request_context.raw_request
            )
            if memories:
                request_context.merge_context(
                    ContextSource.MEMORY,
                    {"memories": memories},
                    relevance=0.8
                )
        except Exception as e:
            logger.error(f"Memory context retrieval failed: {e}")
            
    async def _get_rag_context(self, request_context: RequestContext):
        """Get context from RAG system."""
        try:
            if self.tool_manager.should_use_rag(request_context.raw_request):
                chunks = await self.tool_manager.get_rag_context(
                    request_context.raw_request
                )
                if chunks:
                    request_context.merge_context(
                        ContextSource.RAG,
                        {
                            "chunks": chunks,
                            "chunk_count": len(chunks)
                        },
                        relevance=0.9
                    )
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}")
            
    async def _get_web_context(self, request_context: RequestContext):
        """Get context from web search."""
        try:
            if self.tool_manager.should_use_web_search(request_context.raw_request):
                results = await self.tool_manager.get_web_search_results(
                    request_context.raw_request
                )
                if results:
                    request_context.merge_context(
                        ContextSource.WEB,
                        {
                            "results": results,
                            "result_count": len(results)
                        },
                        relevance=0.7
                    )
        except Exception as e:
            logger.error(f"Web context retrieval failed: {e}")
            
    async def _get_system_context(self, request_context: RequestContext):
        """Get system-level context."""
        try:
            system_context = {
                "available_tools": self.tool_manager.list_tools(),
                "tool_categories": self.tool_manager.get_tool_categories(),
                "request_type": request_context.request_type
            }
            request_context.merge_context(
                ContextSource.SYSTEM,
                system_context,
                relevance=1.0
            )
        except Exception as e:
            logger.error(f"System context retrieval failed: {e}")
            
    async def _select_strategy(
        self,
        request_context: RequestContext
    ) -> Optional[Strategy]:
        """Select appropriate strategy based on context."""
        try:
            # Get merged context
            context = request_context.get_merged_context()
            
            # Get available tools
            available_tools = context.get(
                "available_tools",
                self.tool_manager.list_tools()
            )
            
            # Add request type to context
            context["request_type"] = request_context.request_type
            
            # Select strategy
            strategy = await self.strategy_manager.select_strategy(
                context,
                available_tools
            )
            
            return strategy
            
        except Exception as e:
            logger.error(f"Strategy selection failed: {e}")
            return None
            
    async def _execute_with_retries(
        self,
        strategy: Strategy,
        request_context: RequestContext
    ) -> Dict[str, Any]:
        """Execute strategy with retry logic."""
        retries = 0
        last_error = None
        
        while retries <= self.config.max_retries:
            try:
                # Create tool executor
                tool_executor = self._create_tool_executor()
                
                # Get merged context
                context = request_context.get_merged_context()
                
                # Execute strategy
                result = await self.strategy_manager.execute_strategy(
                    strategy,
                    context,
                    tool_executor
                )
                
                # Optimize if needed
                if self.config.enable_optimization:
                    result = await self._optimize_result(result)
                    
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
        
    async def _optimize_result(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize execution result."""
        try:
            # Optimize tool chain if present
            if "chain" in result:
                result["chain"] = await self.tool_manager.optimize_tool_chain(
                    result["chain"]
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Result optimization failed: {e}")
            return result
            
    async def _update_memory_and_learn(
        self,
        request: str,
        request_context: RequestContext,
        result: Dict[str, Any],
        strategy: Strategy
    ) -> Optional[str]:
        """Update memory and learn from interaction."""
        try:
            # Get merged context
            context = request_context.get_merged_context()
            
            # Add request metadata
            context.update({
                "request_type": request_context.request_type,
                "request_id": request_context.request_id,
                "timestamp": request_context.timestamp.isoformat()
            })
            
            # Store interaction in memory
            memory_id = await self.memory_manager.store_interaction(
                user_input=request,
                context=context,
                result=result
            )
            
            # Learn from interaction
            await self.context_manager.learn_patterns(
                request,
                context,
                result
            )
            
            # Update strategy metrics
            await self.strategy_manager._update_metrics(
                strategy,
                result
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Memory update and learning failed: {e}")
            return None
            
    async def handle_error(
        self,
        error: Exception
    ) -> ExecutionResult:
        """Handle errors with sophisticated error recovery."""
        try:
            # Classify error
            error_info = self._classify_error(error)
            self.errors[error_info.error_id] = error_info
            
            # Get recovery strategy
            recovery_strategy = self._get_recovery_strategy(error_info)
            if not recovery_strategy:
                return self._create_error_result(error_info)
                
            # Execute recovery strategy
            recovery_result = await self._execute_recovery_strategy(
                recovery_strategy,
                error_info
            )
            
            # Update error info
            error_info.recovery_attempts += 1
            error_info.resolved = recovery_result.success
            
            return recovery_result
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            return ExecutionResult(
                success=False,
                result={},
                context=self._create_error_context(str(e)),
                error=f"Error handling failed: {str(e)}"
            )
            
    def _classify_error(self, error: Exception) -> ErrorInfo:
        """Classify an error and create error info."""
        error_id = f"err_{datetime.now().timestamp()}"
        
        # Determine error category and severity
        category, severity = self._analyze_error(error)
        
        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            details={
                "error_type": type(error).__name__,
                "traceback": self._get_error_details(error)
            }
        )
        
    def _analyze_error(self, error: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Analyze error to determine category and severity."""
        error_type = type(error).__name__
        
        # Determine category
        if isinstance(error, (AgentError, SystemError)):
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.CRITICAL
        elif isinstance(error, ContextError):
            category = ErrorCategory.CONTEXT
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, StrategyError):
            category = ErrorCategory.STRATEGY
            severity = ErrorSeverity.HIGH
        elif "Tool" in error_type:
            category = ErrorCategory.TOOL
            severity = ErrorSeverity.HIGH
        elif "Memory" in error_type:
            category = ErrorCategory.MEMORY
            severity = ErrorSeverity.MEDIUM
        elif "RAG" in error_type:
            category = ErrorCategory.RAG
            severity = ErrorSeverity.MEDIUM
        elif "Web" in error_type:
            category = ErrorCategory.WEB
            severity = ErrorSeverity.LOW
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.HIGH
            
        return category, severity
        
    def _get_error_details(self, error: Exception) -> Dict[str, Any]:
        """Get detailed error information."""
        import traceback
        return {
            "traceback": traceback.format_exc(),
            "args": getattr(error, "args", []),
            "message": str(error)
        }
        
    def _get_recovery_strategy(
        self,
        error_info: ErrorInfo
    ) -> Optional[RecoveryStrategy]:
        """Get appropriate recovery strategy for an error."""
        # Check if we have a specific strategy for this category
        strategy = self.recovery_strategies.get(f"{error_info.category}_recovery")
        
        # If no specific strategy, try to find a suitable one
        if not strategy:
            strategies = [
                s for s in self.recovery_strategies.values()
                if s.error_category == error_info.category and
                s.severity >= error_info.severity
            ]
            if strategies:
                # Use the strategy with highest success rate
                strategy = max(strategies, key=lambda s: s.success_rate)
                
        return strategy
        
    async def _execute_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        error_info: ErrorInfo
    ) -> ExecutionResult:
        """Execute a recovery strategy."""
        context = self._create_error_context(error_info)
        
        for action in strategy.actions:
            try:
                # Execute recovery action
                result = await self._execute_recovery_action(
                    action["action"],
                    action["params"],
                    context
                )
                
                # If action succeeds, continue with next action
                if result.get("success", False):
                    context.update(result)
                else:
                    # If action fails, return error result
                    return self._create_error_result(error_info)
                    
            except Exception as e:
                logger.error(f"Recovery action failed: {e}")
                return self._create_error_result(error_info)
                
        # All actions completed successfully
        return ExecutionResult(
            success=True,
            result={"recovery": "successful", "actions": strategy.actions},
            context=self._create_request_context_from_dict(context),
            strategy_id=strategy.strategy_id
        )
        
    async def _execute_recovery_action(
        self,
        action: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single recovery action."""
        try:
            if action == "clear_context":
                return await self._clear_context(context)
            elif action == "rebuild_context":
                return await self._rebuild_context(context, params)
            elif action == "validate_context":
                return await self._validate_context(context)
            elif action == "validate_tool":
                return await self._validate_tool(context)
            elif action == "retry_execution":
                return await self._retry_execution(context, params)
            elif action == "find_alternative_tool":
                return await self._find_alternative_tool(context)
            elif action == "validate_memory":
                return await self._validate_memory(context)
            elif action == "cleanup_memory":
                return await self._cleanup_memory(context)
            elif action == "rebuild_index":
                return await self._rebuild_index(context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Recovery action {action} failed: {e}")
            return {"success": False, "error": str(e)}
            
    def _create_error_context(self, error_info: Union[ErrorInfo, str]) -> Dict[str, Any]:
        """Create context for error handling."""
        if isinstance(error_info, str):
            error_dict = {
                "error_message": error_info,
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_dict = {
                "error_id": error_info.error_id,
                "error_category": error_info.category,
                "error_severity": error_info.severity,
                "error_message": error_info.message,
                "error_details": error_info.details,
                "timestamp": error_info.timestamp.isoformat()
            }
            
        return {
            "error": error_dict,
            "available_tools": self.tool_manager.list_tools(),
            "request_type": RequestType.SYSTEM
        }
        
    def _create_error_result(self, error_info: ErrorInfo) -> ExecutionResult:
        """Create error execution result."""
        return ExecutionResult(
            success=False,
            result={"error": error_info.message},
            context=self._create_request_context_from_dict(
                self._create_error_context(error_info)
            ),
            error=error_info.message
        )
        
    def _create_request_context_from_dict(
        self,
        context_dict: Dict[str, Any]
    ) -> RequestContext:
        """Create RequestContext from dictionary."""
        return RequestContext(
            request_id=f"ctx_{datetime.now().timestamp()}",
            request_type=context_dict.get("request_type", RequestType.SYSTEM),
            raw_request=context_dict.get("error", {}).get("error_message", ""),
            metadata=context_dict
        )
        
    # Recovery action implementations
    async def _clear_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear problematic context."""
        return {"success": True, "cleared_context": True}
        
    async def _rebuild_context(
        self,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rebuild context using fallback methods."""
        try:
            use_fallback = params.get("use_fallback", True)
            new_context = {}
            
            # Add basic context
            new_context.update(await self._get_system_context(
                self._create_request_context_from_dict(context)
            ))
            
            if use_fallback:
                # Add fallback context sources
                if self.config.enable_rag:
                    rag_context = await self._get_rag_context(
                        self._create_request_context_from_dict(context)
                    )
                    new_context.update(rag_context)
                    
            return {
                "success": True,
                "rebuilt_context": new_context
            }
            
        except Exception as e:
            logger.error(f"Context rebuild failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context structure and content."""
        try:
            # Validate required fields
            required_fields = ["available_tools", "request_type"]
            missing_fields = [
                field for field in required_fields
                if field not in context
            ]
            
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {missing_fields}"
                }
                
            return {"success": True, "validated": True}
            
        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _validate_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool availability and configuration."""
        try:
            tools = self.tool_manager.list_tools()
            if not tools:
                return {
                    "success": False,
                    "error": "No tools available"
                }
                
            return {
                "success": True,
                "available_tools": tools
            }
            
        except Exception as e:
            logger.error(f"Tool validation failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _retry_execution(
        self,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry failed execution with modified parameters."""
        try:
            use_fallback = params.get("use_fallback", True)
            
            if use_fallback:
                # Modify context for fallback execution
                context["use_fallback"] = True
                context["retry_count"] = context.get("retry_count", 0) + 1
                
            return {
                "success": True,
                "retry_prepared": True,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Execution retry preparation failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _find_alternative_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find alternative tool for failed execution."""
        try:
            # Get tool categories
            categories = self.tool_manager.get_tool_categories()
            
            # Get available tools by category
            tools_by_category = {
                category: self.tool_manager.list_tools(category)
                for category in categories
            }
            
            return {
                "success": True,
                "alternative_tools": tools_by_category
            }
            
        except Exception as e:
            logger.error(f"Alternative tool search failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _validate_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory system."""
        try:
            memory_stats = await self.memory_manager.get_stats()
            if not memory_stats:
                return {
                    "success": False,
                    "error": "Memory system validation failed"
                }
                
            return {
                "success": True,
                "memory_stats": memory_stats
            }
            
        except Exception as e:
            logger.error(f"Memory validation failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _cleanup_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up memory system."""
        try:
            await self.memory_manager.cleanup()
            return {"success": True, "memory_cleaned": True}
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _rebuild_index(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rebuild memory index."""
        try:
            # Optimize memory retrieval (which rebuilds index)
            await self.memory_manager.optimize_retrieval()
            return {"success": True, "index_rebuilt": True}
            
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
            return {"success": False, "error": str(e)}
            
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
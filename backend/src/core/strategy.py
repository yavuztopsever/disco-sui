from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel
import logging
from datetime import datetime
import json
from pathlib import Path
from enum import Enum
from smolagents import Tool

logger = logging.getLogger(__name__)

class StrategyType(str, Enum):
    """Types of strategies available."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    ADAPTIVE = "adaptive"

class StrategyStep(BaseModel):
    """Model for a strategy step."""
    step_id: str
    tool_name: str
    parameters: Dict[str, Any]
    condition: Optional[str] = None
    next_steps: List[str] = []
    fallback_steps: List[str] = []
    timeout_seconds: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

class Strategy(BaseModel):
    """Model for a complete strategy."""
    strategy_id: str
    strategy_type: StrategyType
    description: str
    steps: Dict[str, StrategyStep]
    entry_points: List[str]
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class StrategyConfig:
    """Configuration for strategy execution."""
    def __init__(
        self,
        max_concurrent_steps: int = 4,
        step_timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_optimization: bool = True,
        max_chain_length: int = 10
    ):
        self.max_concurrent_steps = max_concurrent_steps
        self.step_timeout = step_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_optimization = enable_optimization
        self.max_chain_length = max_chain_length

class StrategyManager:
    """Enhanced strategy manager with learning capabilities."""
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.strategies: Dict[str, Strategy] = {}
        self._setup_storage()
        
    def _setup_storage(self):
        """Setup strategy storage."""
        self.config.strategy_storage_path.mkdir(parents=True, exist_ok=True)
        self._load_strategies()
        
    def _load_strategies(self):
        """Load strategies from storage."""
        try:
            for file_path in self.config.strategy_storage_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    strategy_data = json.load(f)
                    strategy = Strategy(**strategy_data)
                    self.strategies[strategy.strategy_id] = strategy
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            
    async def select_strategy(
        self,
        context: Dict[str, Any],
        available_tools: List[str]
    ) -> Optional[Strategy]:
        """Select the best strategy based on context and available tools."""
        try:
            # Filter strategies by available tools
            valid_strategies = [
                s for s in self.strategies.values()
                if self._validate_strategy_tools(s, available_tools)
            ]
            
            if not valid_strategies:
                return None
                
            # Score strategies based on context match and success rate
            scored_strategies = [
                (s, await self._score_strategy(s, context))
                for s in valid_strategies
            ]
            
            # Select the highest scoring strategy
            best_strategy = max(
                scored_strategies,
                key=lambda x: x[1]
            )[0]
            
            return best_strategy
            
        except Exception as e:
            logger.error(f"Strategy selection failed: {e}")
            return None
            
    def _validate_strategy_tools(
        self,
        strategy: Strategy,
        available_tools: List[str]
    ) -> bool:
        """Validate that all tools required by a strategy are available."""
        required_tools = {
            step.tool_name
            for step in strategy.steps.values()
        }
        return all(tool in available_tools for tool in required_tools)
        
    async def _score_strategy(
        self,
        strategy: Strategy,
        context: Dict[str, Any]
    ) -> float:
        """Score a strategy based on context match and success rate."""
        try:
            # Base score from success rate
            base_score = strategy.success_rate
            
            # Context matching score
            context_score = await self._calculate_context_match(
                strategy,
                context
            )
            
            # Usage frequency score
            usage_score = min(strategy.usage_count / 100, 1.0)
            
            # Combine scores with weights
            final_score = (
                base_score * 0.4 +
                context_score * 0.4 +
                usage_score * 0.2
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Strategy scoring failed: {e}")
            return 0.0
            
    async def _calculate_context_match(
        self,
        strategy: Strategy,
        context: Dict[str, Any]
    ) -> float:
        """Calculate how well a strategy matches the given context."""
        try:
            # Extract relevant features from context
            context_type = context.get("input_type", "")
            context_entities = context.get("entities", {})
            
            # Match against strategy metadata
            type_match = (
                1.0 if strategy.metadata.get("input_type") == context_type
                else 0.0
            )
            
            entity_match = sum(
                1.0 for entity_type in strategy.metadata.get("required_entities", [])
                if entity_type in context_entities
            ) / max(
                len(strategy.metadata.get("required_entities", [])),
                1
            )
            
            # Combine scores
            return (type_match + entity_match) / 2
            
        except Exception as e:
            logger.error(f"Context matching failed: {e}")
            return 0.0
            
    async def execute_strategy(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute a strategy using the provided tool executor."""
        results = {}
        
        try:
            if strategy.strategy_type == StrategyType.SEQUENTIAL:
                results = await self._execute_sequential(
                    strategy,
                    context,
                    tool_executor
                )
            elif strategy.strategy_type == StrategyType.PARALLEL:
                results = await self._execute_parallel(
                    strategy,
                    context,
                    tool_executor
                )
            elif strategy.strategy_type == StrategyType.CONDITIONAL:
                results = await self._execute_conditional(
                    strategy,
                    context,
                    tool_executor
                )
            elif strategy.strategy_type == StrategyType.ITERATIVE:
                results = await self._execute_iterative(
                    strategy,
                    context,
                    tool_executor
                )
            elif strategy.strategy_type == StrategyType.ADAPTIVE:
                results = await self._execute_adaptive(
                    strategy,
                    context,
                    tool_executor
                )
                
            # Update strategy metrics
            await self._update_metrics(strategy, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            return {"error": str(e)}
            
    async def _execute_sequential(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute steps sequentially."""
        results = {}
        current_steps = strategy.entry_points.copy()
        
        while current_steps:
            step_id = current_steps.pop(0)
            step = strategy.steps[step_id]
            
            try:
                # Execute step
                step_result = await self._execute_step(
                    step,
                    context,
                    tool_executor
                )
                results[step_id] = step_result
                
                # Add next steps
                if step_result.get("success", False):
                    current_steps.extend(step.next_steps)
                else:
                    current_steps.extend(step.fallback_steps)
                    
            except Exception as e:
                logger.error(f"Sequential step execution failed: {e}")
                results[step_id] = {"error": str(e)}
                
        return results
        
    async def _execute_parallel(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute steps in parallel."""
        import asyncio
        results = {}
        
        try:
            # Group steps for parallel execution
            step_groups = self._group_parallel_steps(
                strategy.steps,
                strategy.entry_points
            )
            
            # Execute each group
            for group in step_groups:
                # Create tasks for each step in the group
                tasks = [
                    self._execute_step(
                        strategy.steps[step_id],
                        context,
                        tool_executor
                    )
                    for step_id in group
                ]
                
                # Execute group in parallel
                group_results = await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )
                
                # Store results
                for step_id, result in zip(group, group_results):
                    if isinstance(result, Exception):
                        results[step_id] = {"error": str(result)}
                    else:
                        results[step_id] = result
                        
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            results["error"] = str(e)
            
        return results
        
    def _group_parallel_steps(
        self,
        steps: Dict[str, StrategyStep],
        entry_points: List[str]
    ) -> List[List[str]]:
        """Group steps for parallel execution."""
        groups = []
        current_group = []
        
        for step_id in entry_points:
            current_group.append(step_id)
            
            if len(current_group) >= self.config.max_concurrent_steps:
                groups.append(current_group)
                current_group = []
                
        if current_group:
            groups.append(current_group)
            
        return groups
        
    async def _execute_conditional(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute steps based on conditions."""
        results = {}
        current_steps = strategy.entry_points.copy()
        
        while current_steps:
            step_id = current_steps.pop(0)
            step = strategy.steps[step_id]
            
            try:
                # Check condition
                if step.condition:
                    if not await self._evaluate_condition(
                        step.condition,
                        context,
                        results
                    ):
                        continue
                        
                # Execute step
                step_result = await self._execute_step(
                    step,
                    context,
                    tool_executor
                )
                results[step_id] = step_result
                
                # Add next steps based on result
                if step_result.get("success", False):
                    current_steps.extend(step.next_steps)
                else:
                    current_steps.extend(step.fallback_steps)
                    
            except Exception as e:
                logger.error(f"Conditional step execution failed: {e}")
                results[step_id] = {"error": str(e)}
                
        return results
        
    async def _execute_iterative(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute steps iteratively until condition is met."""
        results = {}
        iteration = 0
        
        while iteration < strategy.metadata.get("max_iterations", 10):
            iteration_results = {}
            
            for step_id in strategy.entry_points:
                step = strategy.steps[step_id]
                
                try:
                    # Execute step
                    step_result = await self._execute_step(
                        step,
                        context,
                        tool_executor
                    )
                    iteration_results[step_id] = step_result
                    
                except Exception as e:
                    logger.error(f"Iterative step execution failed: {e}")
                    iteration_results[step_id] = {"error": str(e)}
                    
            # Store iteration results
            results[f"iteration_{iteration}"] = iteration_results
            
            # Check termination condition
            if await self._check_iteration_complete(
                iteration_results,
                context,
                strategy
            ):
                break
                
            iteration += 1
            
        return results
        
    async def _execute_adaptive(
        self,
        strategy: Strategy,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute steps with adaptive behavior based on results."""
        results = {}
        current_steps = strategy.entry_points.copy()
        
        while current_steps:
            step_id = current_steps.pop(0)
            step = strategy.steps[step_id]
            
            try:
                # Execute step with retries
                step_result = await self._execute_with_retry(
                    step,
                    context,
                    tool_executor
                )
                results[step_id] = step_result
                
                # Adapt next steps based on results
                adapted_steps = await self._adapt_next_steps(
                    step,
                    step_result,
                    context,
                    strategy
                )
                current_steps.extend(adapted_steps)
                
            except Exception as e:
                logger.error(f"Adaptive step execution failed: {e}")
                results[step_id] = {"error": str(e)}
                
        return results
        
    async def _execute_step(
        self,
        step: StrategyStep,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute a single strategy step."""
        try:
            # Prepare parameters with context
            parameters = self._prepare_parameters(
                step.parameters,
                context
            )
            
            # Execute tool with timeout
            result = await self._execute_with_timeout(
                tool_executor,
                step.tool_name,
                parameters,
                step.timeout_seconds or self.config.step_timeout
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {"error": str(e)}
            
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
        
    async def _execute_with_timeout(
        self,
        executor: Callable,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute a tool with timeout."""
        import asyncio
        
        try:
            result = await asyncio.wait_for(
                executor(tool_name, parameters),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "error": f"Execution timed out after {timeout} seconds"
            }
        except Exception as e:
            return {"error": str(e)}
            
    async def _execute_with_retry(
        self,
        step: StrategyStep,
        context: Dict[str, Any],
        tool_executor: Callable
    ) -> Dict[str, Any]:
        """Execute a step with retry logic."""
        result = None
        retries = 0
        
        while retries <= step.max_retries:
            result = await self._execute_step(
                step,
                context,
                tool_executor
            )
            
            if result.get("success", False):
                break
                
            retries += 1
            if retries <= step.max_retries:
                await asyncio.sleep(self.config.retry_delay * 2 ** retries)  # Exponential backoff
                
        return result
        
    async def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition string."""
        try:
            # Create a safe evaluation context
            eval_context = {
                "context": context,
                "results": results,
                "len": len,
                "sum": sum,
                "any": any,
                "all": all
            }
            
            return eval(condition, {"__builtins__": {}}, eval_context)
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
            
    async def _check_iteration_complete(
        self,
        results: Dict[str, Any],
        context: Dict[str, Any],
        strategy: Strategy
    ) -> bool:
        """Check if iteration should complete."""
        condition = strategy.metadata.get("completion_condition")
        if not condition:
            return True
            
        return await self._evaluate_condition(
            condition,
            context,
            results
        )
        
    async def _adapt_next_steps(
        self,
        current_step: StrategyStep,
        result: Dict[str, Any],
        context: Dict[str, Any],
        strategy: Strategy
    ) -> List[str]:
        """Adapt next steps based on execution results."""
        try:
            if result.get("success", False):
                return current_step.next_steps
                
            # Check if we should retry
            if (
                current_step.retry_count < current_step.max_retries and
                "error" in result
            ):
                current_step.retry_count += 1
                return [current_step.step_id]
                
            # Use fallback steps
            return current_step.fallback_steps
            
        except Exception as e:
            logger.error(f"Step adaptation failed: {e}")
            return []
            
    async def _update_metrics(
        self,
        strategy: Strategy,
        results: Dict[str, Any]
    ):
        """Update strategy metrics based on execution results."""
        try:
            # Calculate success rate
            success_count = sum(
                1 for r in results.values()
                if isinstance(r, dict) and r.get("success", False)
            )
            total_steps = len(results)
            
            if total_steps > 0:
                new_rate = success_count / total_steps
                # Update with moving average
                strategy.success_rate = (
                    strategy.success_rate * 0.9 + new_rate * 0.1
                )
                
            strategy.usage_count += 1
            strategy.last_used = datetime.now()
            
            # Save updated strategy
            await self._save_strategy(strategy)
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
            
    async def optimize_strategies(self):
        """Optimize strategy collection."""
        try:
            # Remove low performing strategies
            self.strategies = {
                sid: strategy
                for sid, strategy in self.strategies.items()
                if strategy.success_rate >= self.config.min_success_rate
            }
            
            # Save remaining strategies
            for strategy in self.strategies.values():
                await self._save_strategy(strategy)
                
        except Exception as e:
            logger.error(f"Strategy optimization failed: {e}")
            
    async def _save_strategy(self, strategy: Strategy):
        """Save a strategy to storage."""
        try:
            file_path = (
                self.config.strategy_storage_path /
                f"{strategy.strategy_id}.json"
            )
            with open(file_path, 'w') as f:
                json.dump(strategy.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save strategy: {e}")
            
    async def cleanup(self):
        """Clean up strategy resources."""
        try:
            # Save all strategies
            for strategy in self.strategies.values():
                await self._save_strategy(strategy)
                
            # Clear runtime strategies
            self.strategies.clear()
            
        except Exception as e:
            logger.error(f"Strategy cleanup failed: {e}") 
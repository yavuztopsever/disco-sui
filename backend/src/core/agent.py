from typing import Dict, List, Optional, Any
import asyncio
from pydantic import BaseModel
from smolagents import Agent, Tool

from .config import Settings
from .exceptions import AgentError
from .tool_manager import ToolManager
from .logging import get_logger

logger = get_logger(__name__)

class AgentResponse(BaseModel):
    """Response from the agent including the action to take and any relevant data."""
    action: str
    data: Dict[str, Any]
    message: Optional[str] = None

class SmolAgent(Agent):
    """Core agent implementation for DiscoSui using smolagents framework."""
    
    def __init__(self, settings: Settings, tool_manager: ToolManager):
        """Initialize the SmolAgent with configuration and tools."""
        super().__init__()
        self.settings = settings
        self.tool_manager = tool_manager
        self.tools: List[Tool] = []
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all available tools from the tool manager."""
        self.tools = self.tool_manager.get_all_tools()
        
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process a user request and return appropriate action and data."""
        try:
            # Get relevant tools based on user input
            relevant_tools = self.tool_manager.get_relevant_tools(user_input)
            
            # Determine if RAG is needed
            if self.tool_manager.should_use_rag(user_input):
                # Get context from vault using RAG
                rag_context = await self.tool_manager.get_rag_context(user_input)
                if context:
                    context.update(rag_context)
                else:
                    context = rag_context

            # Execute tool chain
            result = await self._execute_tool_chain(user_input, relevant_tools, context)
            
            return AgentResponse(
                action=result.get("action", "response"),
                data=result.get("data", {}),
                message=result.get("message")
            )

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise AgentError(f"Failed to process request: {str(e)}")

    async def _execute_tool_chain(
        self, 
        user_input: str, 
        tools: List[Tool], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a chain of tools based on the user input and context."""
        current_context = context or {}
        
        for tool in tools:
            try:
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

            except Exception as e:
                logger.error(f"Error executing tool {tool.name}: {str(e)}")
                raise AgentError(f"Tool execution failed: {str(e)}")

        return current_context

    async def handle_error(self, error: Exception) -> AgentResponse:
        """Handle errors during request processing."""
        error_msg = str(error)
        logger.error(f"Agent error: {error_msg}")
        
        return AgentResponse(
            action="error",
            data={"error": error_msg},
            message=f"An error occurred: {error_msg}"
        )

    def update_tools(self):
        """Update the available tools from the tool manager."""
        self._initialize_tools() 
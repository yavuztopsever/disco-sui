from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel, Field
from ..core.exceptions import LLMError, RAGError, ToolError
from ..core.config import settings
from smolagents import LiteLLMModel, Tool, ToolCallingAgent
import os
import logging
from pathlib import Path
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

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
    def __init__(self):
        """Initialize the ToolManager with built-in smolagents tools and custom tools."""
        self.tools: Dict[str, Any] = {}
        self.registered_tools: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize LLM
        self.llm = LiteLLMModel(
            model_id="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
            max_tokens=1000
        )
        
        # Initialize built-in smolagents tools
        self._initialize_builtin_tools()
        
        # Initialize custom tools only if needed
        self._initialize_custom_tools()

    def _initialize_builtin_tools(self):
        """Initialize built-in smolagents tools."""
        try:
            # Create a ToolCallingAgent to get access to built-in tools
            agent = ToolCallingAgent(
                model=self.llm,
                tools=[],  # Empty list as we'll get built-in tools
                system_prompt="You are a helpful assistant for managing Obsidian vaults."
            )
            
            # Get all available built-in tools
            builtin_tools = agent.get_available_tools()
            
            # Register built-in tools
            for tool_name, tool_info in builtin_tools.items():
                self.register_tool(tool_name, tool_info)
                
            self.logger.info(f"Successfully initialized {len(builtin_tools)} built-in tools")
        except Exception as e:
            self.logger.error(f"Failed to initialize built-in tools: {str(e)}")
            raise ToolError(f"Failed to initialize built-in tools: {str(e)}")

    def _initialize_custom_tools(self):
        """Initialize custom tools only if they don't exist in built-in tools."""
        try:
            # Import custom tools
            from ..tools.note_tools import (
                CreateNoteTool, UpdateNoteTool, DeleteNoteTool,
                ListNotesTool, SearchNotesTool
            )
            from ..tools.semantic_tools import (
                AnalyzeRelationshipsTool, FindRelatedNotesTool,
                GenerateKnowledgeGraphTool
            )
            
            # Define custom tools to check
            custom_tools = {
                "create_note": CreateNoteTool,
                "update_note": UpdateNoteTool,
                "delete_note": DeleteNoteTool,
                "list_notes": ListNotesTool,
                "search_notes": SearchNotesTool,
                "analyze_relationships": AnalyzeRelationshipsTool,
                "find_related_notes": FindRelatedNotesTool,
                "generate_knowledge_graph": GenerateKnowledgeGraphTool
            }
            
            # Register custom tools only if they don't exist
            for tool_name, tool_class in custom_tools.items():
                if tool_name not in self.registered_tools:
                    self.register_tool(tool_name, tool_class(settings.VAULT_PATH))
                    
            self.logger.info(f"Successfully initialized {len(custom_tools)} custom tools")
        except Exception as e:
            self.logger.error(f"Failed to initialize custom tools: {str(e)}")
            raise ToolError(f"Failed to initialize custom tools: {str(e)}")

    def register_tool(self, tool_name: str, tool_instance: Any) -> None:
        """Register a new tool with validation."""
        try:
            # Validate tool instance
            if not isinstance(tool_instance, Tool):
                raise ValueError(f"Tool instance must inherit from smolagents.Tool")
            
            # Validate required attributes
            required_attrs = ['name', 'description', 'inputs', 'output_type']
            for attr in required_attrs:
                if not hasattr(tool_instance, attr):
                    raise ValueError(f"Tool must have {attr} attribute")
            
            # Validate input schema
            if not isinstance(tool_instance.inputs, dict):
                raise ValueError("Tool inputs must be a dictionary")
            
            # Validate output type
            if not isinstance(tool_instance.output_type, str):
                raise ValueError("Tool output_type must be a string")
            
            # Register the tool
            self.registered_tools[tool_name] = tool_instance
            self.tools[tool_name] = {
                "name": tool_name,
                "description": tool_instance.description,
                "inputs": tool_instance.inputs,
                "output_type": tool_instance.output_type,
                "examples": getattr(tool_instance, 'examples', []),
                "error_handling": getattr(tool_instance, 'error_handling', {}),
                "dependencies": getattr(tool_instance, 'dependencies', []),
                "version": getattr(tool_instance, 'version', '1.0.0'),
                "last_updated": datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully registered tool: {tool_name}")
        except Exception as e:
            self.logger.error(f"Failed to register tool {tool_name}: {str(e)}")
            raise ToolError(f"Failed to register tool {tool_name}: {str(e)}")

    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters against the tool's input schema."""
        try:
            tool = self.get_tool(tool_name)
            input_schema = tool.inputs
            
            for param_name, param_value in parameters.items():
                if param_name not in input_schema:
                    raise ValueError(f"Unknown parameter: {param_name}")
                
                param_schema = input_schema[param_name]
                param_type = param_schema.get("type")
                
                if param_type == "string":
                    if not isinstance(param_value, str):
                        raise ValueError(f"Parameter {param_name} must be a string")
                elif param_type == "integer":
                    if not isinstance(param_value, int):
                        raise ValueError(f"Parameter {param_name} must be an integer")
                elif param_type == "array":
                    if not isinstance(param_value, list):
                        raise ValueError(f"Parameter {param_name} must be an array")
                    if "items" in param_schema:
                        item_type = param_schema["items"].get("type")
                        for item in param_value:
                            if item_type == "string" and not isinstance(item, str):
                                raise ValueError(f"Array item in {param_name} must be a string")
                            elif item_type == "integer" and not isinstance(item, int):
                                raise ValueError(f"Array item in {param_name} must be an integer")
                
                # Check for required parameters
                if param_schema.get("required", False) and param_value is None:
                    raise ValueError(f"Required parameter {param_name} is missing")
                
                # Check for enum values if specified
                if "enum" in param_schema and param_value not in param_schema["enum"]:
                    raise ValueError(f"Parameter {param_name} must be one of: {param_schema['enum']}")
            
            return True
        except Exception as e:
            self.logger.error(f"Parameter validation failed for tool {tool_name}: {str(e)}")
            raise ToolError(f"Parameter validation failed for tool {tool_name}: {str(e)}")

    def get_tool(self, tool_name: str) -> Any:
        """Get a registered tool by name with validation."""
        if tool_name not in self.registered_tools:
            raise ToolError(f"Tool {tool_name} not found")
        return self.registered_tools[tool_name]

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
from smolagents import ToolCallingAgent, Tool, LiteLLMModel
import os
from typing import List, Dict, Any, Union, Optional
import re
from pydantic import BaseModel
from datetime import datetime
import logging
from src.core.exceptions import (
    NoteNotFoundError,
    NoteAlreadyExistsError,
    TemplateNotFoundError,
    FrontmatterError,
    NoteManagementError
)
from src.tools.service_tools import trigger_service, TriggerServiceInput
from src.services.service_manager import service_registry, ServiceStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Placeholder classes for missing modules
class RAG:
    def __init__(self):
        pass

class Indexer:
    def __init__(self):
        pass

class SemanticAnalyzer:
    def __init__(self):
        pass

class NoteRequest(BaseModel):
    """Pydantic model for note-related requests."""
    title: Optional[str] = None
    content: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    template: Optional[str] = None

class CreateNoteTool(Tool):
    name = "create_note"
    description = "Create a new note in the vault"
    inputs = {
        "title": {
            "type": "string",
            "description": "The title of the note"
        },
        "content": {
            "type": "string",
            "description": "The content of the note"
        },
        "folder": {
            "type": "string",
            "description": "Optional folder path where to create the note",
            "nullable": True
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path

    def forward(self, title: str, content: str, folder: Optional[str] = "") -> Dict[str, Any]:
        try:
            folder_path = os.path.join(self.vault_path, folder) if folder else self.vault_path
            os.makedirs(folder_path, exist_ok=True)
            
            file_path = os.path.join(folder_path, f"{title}.md")
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"Note '{title}' created successfully",
                "path": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create note: {str(e)}",
                "error": str(e)
            }

class DeleteNoteTool(Tool):
    name = "delete_note"
    description = "Delete a note from the vault"
    inputs = {
        "title": {
            "type": "string",
            "description": "The title of the note to delete"
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path

    def forward(self, title: str) -> Dict[str, Any]:
        try:
            file_path = os.path.join(self.vault_path, f"{title}.md")
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    "success": True,
                    "message": f"Note '{title}' deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Note '{title}' not found"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete note: {str(e)}",
                "error": str(e)
            }

class ListNotesTool(Tool):
    name = "list_notes"
    description = "List all notes in the vault"
    inputs = {}
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path

    def forward(self) -> Dict[str, Any]:
        try:
            notes = []
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.vault_path)
                        notes.append(rel_path)
            return {
                "success": True,
                "notes": notes
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list notes: {str(e)}",
                "error": str(e)
            }

class SearchNotesTool(Tool):
    name = "search_notes"
    description = "Search for notes containing specific text"
    inputs = {
        "query": {
            "type": "string",
            "description": "The text to search for in notes"
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path

    def forward(self, query: str) -> Dict[str, Any]:
        try:
            results = []
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                rel_path = os.path.relpath(file_path, self.vault_path)
                                results.append({
                                    "path": rel_path,
                                    "matches": content.lower().count(query.lower())
                                })
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to search notes: {str(e)}",
                "error": str(e)
            }

class OpenNoteTool(Tool):
    name = "open_note"
    description = "Open a note in Obsidian"
    inputs = {
        "title": {
            "type": "string",
            "description": "The title of the note to open"
        }
    }
    output_type = "object"

    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = vault_path

    def forward(self, title: str) -> Dict[str, Any]:
        try:
            # Construct the Obsidian URI
            uri = f"obsidian://open?vault={os.path.basename(self.vault_path)}&file={title}"
            
            # Open the note using the system's default URI handler
            import subprocess
            subprocess.run(['open', uri], check=True)
            
            return {
                "success": True,
                "message": f"Opened note '{title}' in Obsidian",
                "uri": uri
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open note: {str(e)}",
                "error": str(e)
            }

class TriggerServiceTool(Tool):
    name = "trigger_service"
    description = "Trigger a service to update vault contents"
    inputs = {
        "service_name": {
            "type": "string",
            "description": "Name of the service to trigger"
        },
        "target_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of specific notes to update",
            "nullable": True
        },
        "force_update": {
            "type": "boolean",
            "description": "Whether to force update even if no changes detected",
            "default": False
        },
        "options": {
            "type": "object",
            "description": "Optional service-specific configuration options",
            "nullable": True
        }
    }
    output_type = "object"
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        
    def forward(
        self,
        service_name: str,
        target_notes: Optional[List[str]] = None,
        force_update: bool = False,
        options: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Trigger a service to update vault contents.
        
        Args:
            service_name: Name of the service to trigger
            target_notes: Optional list of specific notes to update
            force_update: Whether to force update even if no changes detected
            options: Optional service-specific configuration options
            
        Returns:
            Dict containing the result of the service trigger operation
            
        Raises:
            ValueError: If service is not found or is already running
            Exception: If service execution fails
        """
        try:
            input_data = TriggerServiceInput(
                service_name=service_name,
                target_notes=target_notes,
                force_update=force_update,
                options=options
            )
            
            trigger_service(input_data)
            
            # Get service status after triggering
            status = service_registry.get_status(service_name)
            last_run = service_registry.get_last_run(service_name)
            
            return {
                "success": True,
                "service": service_name,
                "status": status.value,
                "last_run": last_run.isoformat() if last_run else None,
                "message": f"Service {service_name} triggered successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
                "message": f"Failed to trigger service {service_name}"
            }

class NoteManagementAgent(ToolCallingAgent):
    """NoteManagementAgent manages Obsidian vault operations through natural language interaction.
    
    This agent provides comprehensive note management capabilities including:
    - Note creation, deletion, and modification
    - Folder management
    - Tag management
    - Template management
    - Audio and email processing
    - Semantic analysis and RAG
    - Vault organization
    
    Attributes:
        vault_path (str): Path to the Obsidian vault
        plugin_path (str): Path to the DiscoSui plugin directory
        rag (RAG): Retrieval Augmented Generation component
        indexer (Indexer): Note indexing component
        semantic_analyzer (SemanticAnalyzer): Semantic analysis component
        tool_usage_stats (Dict): Statistics about tool usage
    """
    
    def __init__(self, vault_path: str):
        """Initialize the NoteManagementAgent with a vault path.
        
        Args:
            vault_path (str): Path to the Obsidian vault
            
        Raises:
            NoteManagementError: If initialization fails
        """
        try:
            self.vault_path = vault_path
            self.plugin_path = os.path.join(vault_path, '.obsidian', 'plugins', 'discosui')
            
            logger.info(f"Initializing NoteManagementAgent with vault path: {vault_path}")
            
            # Initialize RAG and indexing components
            try:
                self.rag = RAG()
                self.indexer = Indexer()
                self.semantic_analyzer = SemanticAnalyzer()
                logger.info("Successfully initialized RAG and indexing components")
            except Exception as e:
                logger.error(f"Failed to initialize RAG components: {str(e)}")
                raise NoteManagementError(f"Failed to initialize RAG components: {str(e)}")

            # Initialize all available tools
            try:
                tools = [
                    # Note Management Tools
                    CreateNoteTool(vault_path),
                    DeleteNoteTool(vault_path),
                    ListNotesTool(vault_path),
                    SearchNotesTool(vault_path),
                    UpdateNoteTool(vault_path),
                    
                    # Folder Management Tools
                    CreateFolderTool(vault_path),
                    DeleteFolderTool(vault_path),
                    MoveFolderTool(vault_path),
                    ListFoldersTool(vault_path),
                    GetFolderContentsTool(vault_path),
                    
                    # Tag Management Tools
                    TagManagerTool(vault_path),
                    
                    # Template Management Tools
                    CreateTemplateTool(vault_path),
                    DeleteTemplateTool(vault_path),
                    ListTemplatesTool(vault_path),
                    ApplyTemplateTool(vault_path),
                    GetTemplateContentTool(vault_path),
                    
                    # Audio Processing Tools
                    TranscribeAudioTool(vault_path),
                    ListAudioFilesTool(vault_path),
                    GetTranscriptionNoteTool(vault_path),
                    
                    # Email Processing Tools
                    ProcessEmailTool(vault_path),
                    ListEmailFilesTool(vault_path),
                    GetEmailNoteTool(vault_path),
                    
                    # Indexing and Search Tools
                    IndexNoteTool(vault_path),
                    ClusterNotesTool(vault_path),
                    
                    # Semantic Analysis Tools
                    AnalyzeRelationshipsTool(vault_path),
                    FindRelatedNotesTool(vault_path),
                    GenerateKnowledgeGraphTool(vault_path),
                    
                    # Vault Reorganization Tools
                    AnalyzeVaultStructureTool(vault_path),
                    ReorganizeVaultTool(vault_path),
                    SuggestOrganizationTool(vault_path),
                    
                    # Hierarchy Management Tools
                    HierarchyManagerTool(vault_path),
                    
                    # Additional Tools
                    OpenNoteTool(vault_path),
                    TriggerServiceTool(vault_path)
                ]
                logger.info("Successfully initialized all tools")
            except Exception as e:
                logger.error(f"Failed to initialize tools: {str(e)}")
                raise NoteManagementError(f"Failed to initialize tools: {str(e)}")

            # Initialize parent class
            try:
                super().__init__(
                    model=LiteLLMModel(
                        model_id="gpt-4",
                        api_key=os.getenv("OPENAI_API_KEY"),
                        temperature=0.7,
                        max_tokens=1000,
                        request_timeout=30
                    ),
                    tools=tools,
                    system_prompt="""You are DiscoSui, an intelligent assistant for managing Obsidian vaults.
                    Your role is to help users interact with their notes through natural language.
                    
                    Available Capabilities:
                    1. Note Management:
                       - Create, update, and delete notes
                       - Search for notes using semantic search
                       - List and organize notes
                       - Apply templates to notes
                    
                    2. Folder Management:
                       - Create, delete, and move folders
                       - List folder contents
                       - Organize notes in folders
                    
                    3. Tag Management:
                       - Add, remove, and search by tags
                       - Get tag statistics
                       - Find related tags
                       - Suggest tags based on content
                    
                    4. Template Management:
                       - Create and manage templates
                       - Apply templates to notes
                       - Validate template usage
                    
                    5. Content Processing:
                       - Transcribe audio files to notes
                       - Process and organize emails
                       - Generate knowledge graphs
                       - Analyze relationships between notes
                    
                    6. Vault Organization:
                       - Analyze vault structure
                       - Suggest organization improvements
                       - Reorganize content
                       - Maintain hierarchy
                    
                    7. Semantic Analysis:
                       - Find related notes
                       - Analyze content relationships
                       - Generate insights
                       - Answer questions using RAG
                    
                    Always:
                    1. Maintain a conversational tone
                    2. Provide helpful, context-aware responses
                    3. Ask for clarification when needed
                    4. Follow vault structure and templates
                    5. Consider opening relevant notes automatically
                    6. Use appropriate tools for each task
                    7. Handle errors gracefully
                    8. Provide clear feedback and next steps"""
                )
                logger.info("Successfully initialized parent class")
            except Exception as e:
                logger.error(f"Failed to initialize parent class: {str(e)}")
                raise NoteManagementError(f"Failed to initialize parent class: {str(e)}")

            # Setup plugin and initialize knowledge base
            self._ensure_plugin_setup()
            self._initialize_knowledge_base()
            
            # Initialize tool usage tracking
            self.tool_usage_stats = {}
            logger.info("NoteManagementAgent initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NoteManagementAgent: {str(e)}")
            raise NoteManagementError(f"Failed to initialize NoteManagementAgent: {str(e)}")

    def _initialize_knowledge_base(self):
        """Initialize the knowledge base by indexing all notes.
        
        Raises:
            NoteManagementError: If knowledge base initialization fails
        """
        try:
            logger.info("Starting knowledge base initialization")
            self.indexer.index_directory(self.vault_path)
            logger.info("Successfully initialized knowledge base")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            raise NoteManagementError(f"Failed to initialize knowledge base: {str(e)}")

    def _ensure_plugin_setup(self):
        """Ensure the Obsidian plugin directory structure exists.
        
        Raises:
            NoteManagementError: If plugin setup fails
        """
        try:
            logger.info("Setting up plugin directory structure")
            os.makedirs(self.plugin_path, exist_ok=True)
            manifest_path = os.path.join(self.plugin_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                self._create_manifest()
            logger.info("Successfully set up plugin directory structure")
        except Exception as e:
            logger.error(f"Failed to set up plugin directory: {str(e)}")
            raise NoteManagementError(f"Failed to set up plugin directory: {str(e)}")

    def _create_manifest(self):
        """Create the plugin manifest file."""
        manifest = {
            "id": "discosui",
            "name": "DiscoSui",
            "version": "1.0.0",
            "minAppVersion": "0.15.0",
            "description": "AI-powered note management interface for Obsidian",
            "author": "DiscoSui Team",
            "authorUrl": "https://github.com/yourusername/discosui",
            "isDesktopOnly": False,
            "fundingUrl": {
                "Buy Me a Coffee": "https://buymeacoffee.com/yourusername"
            }
        }
        with open(os.path.join(self.plugin_path, 'manifest.json'), 'w') as f:
            import json
            json.dump(manifest, f, indent=2)

    def _track_tool_usage(self, tool_name: str, success: bool, error: Optional[str] = None):
        """Track tool usage statistics.
        
        Args:
            tool_name (str): Name of the tool
            success (bool): Whether the tool execution was successful
            error (Optional[str]): Error message if the tool execution failed
        """
        try:
            if tool_name not in self.tool_usage_stats:
                self.tool_usage_stats[tool_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "last_used": None,
                    "common_errors": {}
                }
            
            stats = self.tool_usage_stats[tool_name]
            stats["total_calls"] += 1
            stats["last_used"] = datetime.now().isoformat()
            
            if success:
                stats["successful_calls"] += 1
                logger.info(f"Tool {tool_name} executed successfully")
            else:
                stats["failed_calls"] += 1
                if error:
                    if error not in stats["common_errors"]:
                        stats["common_errors"][error] = 0
                    stats["common_errors"][error] += 1
                logger.warning(f"Tool {tool_name} execution failed: {error}")
        except Exception as e:
            logger.error(f"Failed to track tool usage: {str(e)}")

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message and return an appropriate response.
        
        Args:
            message (str): The user's message to process
            
        Returns:
            Dict[str, Any]: The response containing success status, message, and any relevant data
            
        Raises:
            NoteManagementError: If message processing fails
        """
        try:
            logger.info(f"Processing message: {message}")
            
            # Use the LLM to understand the intent
            try:
                intent_response = await self.model.generate(self._create_intent_prompt(message))
                intent_data = intent_response.json()
                logger.info(f"Successfully analyzed message intent: {intent_data['intent']}")
            except Exception as e:
                logger.error(f"Failed to analyze message intent: {str(e)}")
                raise NoteManagementError(f"Failed to analyze message intent: {str(e)}")

            # Create NoteRequest object
            try:
                note_request = NoteRequest(**intent_data["parameters"])
                logger.info("Successfully created note request")
            except Exception as e:
                logger.error(f"Failed to create note request: {str(e)}")
                raise NoteManagementError(f"Failed to create note request: {str(e)}")

            # Track tool usage and process the request
            result = await self._process_intent(intent_data, note_request)
            logger.info("Successfully processed message")
            return result

        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            return self._format_error_response(str(e), "An error occurred while processing your request")

    def _create_intent_prompt(self, message: str) -> str:
        """Create the prompt for intent analysis.
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The formatted prompt for intent analysis
        """
        return f"""Analyze the following user message and determine:
        1. The primary intent (create, read, update, delete, search, analyze, question, organize, process)
        2. Any relevant parameters (title, content, folder, tags, template)
        3. Any additional context or requirements
        4. Whether any notes should be automatically opened
        5. Which specific tools would be most appropriate
        6. Any potential errors or edge cases to handle

        Message: {message}

        Format your response as JSON with the following structure:
        {{
            "intent": "string",
            "parameters": {{
                "title": "string or null",
                "content": "string or null",
                "folder": "string or null",
                "tags": ["string"],
                "template": "string or null"
            }},
            "context": "string",
            "auto_open_notes": ["string"],
            "recommended_tools": ["string"],
            "potential_errors": ["string"]
        }}"""

    async def _process_intent(self, intent_data: Dict[str, Any], note_request: NoteRequest) -> Dict[str, Any]:
        """Process the analyzed intent and execute appropriate actions.
        
        Args:
            intent_data (Dict[str, Any]): The analyzed intent data
            note_request (NoteRequest): The note request object
            
        Returns:
            Dict[str, Any]: The response containing success status, message, and any relevant data
            
        Raises:
            NoteManagementError: If intent processing fails
        """
        try:
            # Track tool usage
            for tool_name in intent_data.get("recommended_tools", []):
                self._track_tool_usage(tool_name, True)

            # Handle question intent
            if intent_data["intent"] == "question":
                return await self._handle_question_intent(message, intent_data)

            # Handle other intents
            return await self._handle_general_intent(intent_data, note_request)

        except Exception as e:
            logger.error(f"Failed to process intent: {str(e)}")
            raise NoteManagementError(f"Failed to process intent: {str(e)}")

    def _format_response(self, result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Format the tool response into a conversational message.
        
        Args:
            result (Dict[str, Any]): The raw result from tool execution
            context (str): The context of the request
            
        Returns:
            Dict[str, Any]: The formatted response
        """
        try:
            if not result.get("success", False):
                logger.warning(f"Tool execution failed: {result.get('error', 'Unknown error')}")
                return self._format_error_response(result.get("error", "Unknown error"), context)

            response = self.model.generate(self._create_response_prompt(result, context))
            logger.info("Successfully formatted response")
            
            return {
                "success": True,
                "response": response,
                "context": context,
                "data": result
            }
        except Exception as e:
            logger.error(f"Failed to format response: {str(e)}")
            return self._format_error_response(str(e), context)

    def _format_error_response(self, error: str, context: str) -> Dict[str, Any]:
        """Format an error response with helpful suggestions.
        
        Args:
            error (str): The error message
            context (str): The context of the request
            
        Returns:
            Dict[str, Any]: The formatted error response
        """
        logger.error(f"Formatting error response: {error}")
        return {
            "success": False,
            "error": error,
            "response": f"I encountered an error: {error}. {context}",
            "suggestions": [
                "Please check if all required parameters are provided",
                "Verify that the note or folder exists",
                "Ensure you have the necessary permissions",
                "Try rephrasing your request"
            ]
        }

    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage.
        
        Returns:
            Dict[str, Any]: Tool usage statistics
        """
        return self.tool_usage_stats

    async def run(self, task: str) -> Union[Dict[str, Any], str]:
        """Run the agent on a given task.
        
        Args:
            task (str): The task to run
            
        Returns:
            Union[Dict[str, Any], str]: The result of running the task
        """
        try:
            logger.info(f"Running task: {task}")
            result = await self.process_message(task)
            logger.info("Successfully completed task")
            return result
        except Exception as e:
            logger.error(f"Failed to run task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Could you please try again?"
            }
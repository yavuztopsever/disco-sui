from smolagents import ToolCallingAgent, Tool, LiteLLMModel
import os
from typing import List, Dict, Any, Union, Optional
import re
from pydantic import BaseModel
from ..features.indexing.rag import RAG
from ..features.indexing.indexer import Indexer
from ..features.semantic_analysis.semantic_analyzer import SemanticAnalyzer
from datetime import datetime

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

class NoteManagementAgent(ToolCallingAgent):
    def __init__(self, vault_path: str):
        """Initialize the NoteManagementAgent with a vault path."""
        self.vault_path = vault_path
        self.plugin_path = os.path.join(vault_path, '.obsidian', 'plugins', 'discosui')
        
        # Initialize RAG and indexing components
        self.rag = RAG()
        self.indexer = Indexer()
        self.semantic_analyzer = SemanticAnalyzer()
        
        # Initialize all available tools
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
            OpenNoteTool(vault_path)
        ]
        
        # Initialize parent class with tools and enhanced system prompt
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
        
        # Setup plugin after parent initialization
        self._ensure_plugin_setup()
        
        # Initialize the knowledge base
        self._initialize_knowledge_base()
        
        # Initialize tool usage tracking
        self.tool_usage_stats = {}

    def _initialize_knowledge_base(self):
        """Initialize the knowledge base by indexing all notes."""
        try:
            # Index all notes in the vault
            self.indexer.index_directory(self.vault_path)
        except Exception as e:
            print(f"Warning: Error initializing knowledge base: {str(e)}")

    def _ensure_plugin_setup(self):
        """Ensure the Obsidian plugin directory structure exists."""
        os.makedirs(self.plugin_path, exist_ok=True)
        manifest_path = os.path.join(self.plugin_path, 'manifest.json')
        if not os.path.exists(manifest_path):
            self._create_manifest()

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
        """Track tool usage statistics."""
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
        else:
            stats["failed_calls"] += 1
            if error:
                if error not in stats["common_errors"]:
                    stats["common_errors"][error] = 0
                stats["common_errors"][error] += 1

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a natural language message and return an appropriate response."""
        try:
            # Use the LLM to understand the intent and extract relevant information
            intent_prompt = f"""Analyze the following user message and determine:
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

            # Get intent analysis from LLM
            intent_response = await self.model.generate(intent_prompt)
            intent_data = intent_response.json()

            # Create a NoteRequest object from the extracted parameters
            note_request = NoteRequest(**intent_data["parameters"])

            # Track tool usage
            for tool_name in intent_data.get("recommended_tools", []):
                self._track_tool_usage(tool_name, True)

            # Open relevant notes if specified
            if intent_data.get("auto_open_notes"):
                open_tool = next((t for t in self.tools if t.name == "open_note"), None)
                if open_tool:
                    for note_title in intent_data["auto_open_notes"]:
                        try:
                            await open_tool.forward(title=note_title)
                            self._track_tool_usage("open_note", True)
                        except Exception as e:
                            self._track_tool_usage("open_note", False, str(e))

            # Route to appropriate tool based on intent
            if intent_data["intent"] == "question":
                # Use RAG for question answering
                response = self.rag.process_query(message)
                
                # Open relevant notes from RAG response
                if response.notes_to_open:
                    open_tool = next((t for t in self.tools if t.name == "open_note"), None)
                    if open_tool:
                        for note_title in response.notes_to_open:
                            try:
                                await open_tool.forward(title=note_title)
                                self._track_tool_usage("open_note", True)
                            except Exception as e:
                                self._track_tool_usage("open_note", False, str(e))
                
                return self._format_response(response.dict(), intent_data["context"])
            
            # Handle other intents with appropriate tools
            tool = next((t for t in self.tools if t.name in intent_data.get("recommended_tools", [])), None)
            if tool:
                try:
                    result = await tool.forward(**note_request.dict(exclude_none=True))
                    self._track_tool_usage(tool.name, True)
                    return self._format_response(result, intent_data["context"])
                except Exception as e:
                    self._track_tool_usage(tool.name, False, str(e))
                    return self._format_error_response(str(e), intent_data["context"])
            
            # Default response for unrecognized intents
            return {
                "success": True,
                "response": "I understand you want to interact with your notes, but I'm not sure exactly what you'd like to do. Could you please clarify your request?",
                "context": intent_data["context"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Could you please try rephrasing it?"
            }

    def _format_response(self, result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Format the tool response into a conversational message."""
        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "response": "I encountered an error while processing your request. Could you please try again?"
            }

        # Create a conversational response based on the result and context
        response_prompt = f"""Based on the following result and context, create a natural, conversational response:

        Result: {result}
        Context: {context}

        The response should:
        1. Acknowledge the user's request
        2. Explain what was done
        3. Provide relevant details from the result
        4. Mention any notes that were opened
        5. Suggest next steps if appropriate

        Response:"""

        # Get conversational response from LLM
        response = self.model.generate(response_prompt)
        
        return {
            "success": True,
            "response": response,
            "context": context,
            "data": result
        }

    def _format_error_response(self, error: str, context: str) -> Dict[str, Any]:
        """Format an error response with helpful suggestions."""
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
        """Get statistics about tool usage."""
        return self.tool_usage_stats

    async def run(self, task: str) -> Union[Dict[str, Any], str]:
        """Run the agent on a given task."""
        try:
            result = await self.process_message(task)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your request. Could you please try again?"
            }
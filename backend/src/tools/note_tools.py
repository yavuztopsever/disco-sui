from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
from ..services.content.notes import NoteManager
from ..services.organization.folders import FolderManager
from pathlib import Path
from datetime import datetime
import asyncio
from smolagents import Tool
from pydantic import BaseModel, ConfigDict
from ..core.exceptions import NoteManagementError

class NoteInput(BaseModel):
    """Input for note manipulation tools."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    title: str
    content: Optional[str] = None
    folder: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NoteOutput(BaseModel):
    """Output from note manipulation tools."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    path: str
    success: bool
    message: Optional[str] = None


class NoteTool:
    """Base class for note manipulation tools."""
    
    def __init__(self, note_manager: NoteManager):
        """Initialize the note tool.
        
        Args:
            note_manager: Note manager instance
        """
        self.note_manager = note_manager
    
    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """Execute the note tool.
        
        Args:
            input_data: Input data for note manipulation
            
        Returns:
            Output containing operation result
            
        Raises:
            NoteManagementError: If operation fails
        """
        raise NotImplementedError("NoteTool.execute must be implemented by subclasses")


class CreateNoteTool(NoteTool):
    """Tool for creating new notes."""
    
    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """Create a new note.
        
        Args:
            input_data: Input data for note creation
            
        Returns:
            Output containing creation result
            
        Raises:
            NoteManagementError: If creation fails
        """
        try:
            path = await self.note_manager.create_note(
                title=input_data.title,
                content=input_data.content,
                folder=input_data.folder,
                metadata=input_data.metadata
            )
            return NoteOutput(
                path=str(path),
                success=True,
                message="Note created successfully"
            )
        except Exception as e:
            raise NoteManagementError(f"Failed to create note: {str(e)}")


class UpdateNoteTool(NoteTool):
    """Tool for updating existing notes."""
    
    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """Update an existing note.
        
        Args:
            input_data: Input data for note update
            
        Returns:
            Output containing update result
            
        Raises:
            NoteManagementError: If update fails
        """
        try:
            path = await self.note_manager.update_note(
                title=input_data.title,
                content=input_data.content,
                metadata=input_data.metadata
            )
            return NoteOutput(
                path=str(path),
                success=True,
                message="Note updated successfully"
            )
        except Exception as e:
            raise NoteManagementError(f"Failed to update note: {str(e)}")


class DeleteNoteTool(NoteTool):
    """Tool for deleting notes."""
    
    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """Delete a note.
        
        Args:
            input_data: Input data for note deletion
            
        Returns:
            Output containing deletion result
            
        Raises:
            NoteManagementError: If deletion fails
        """
        try:
            path = await self.note_manager.delete_note(input_data.title)
            return NoteOutput(
                path=str(path),
                success=True,
                message="Note deleted successfully"
            )
        except Exception as e:
            raise NoteManagementError(f"Failed to delete note: {str(e)}")

class NotesTool(BaseTool):
    """Note management tool following smolagents Tool interface.
    
    This implements the NotesTool functionality from Flow 2 in flows.md.
    It supports semantic access to notes with vector and graph-based search.
    """
    
    def __init__(self, vault_path: str):
        """Initialize the note manager tool.
        
        Args:
            vault_path: Path to the Obsidian vault
        """
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        self.folder_manager = FolderManager(vault_path)
        
        # These would be initialized in practice
        self.vector_db = None
        self.graph_db = None
        self.embedding_model = None
        self.semantic_analyzer = None
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "NotesTool"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Semantic note access, creation, editing and management for Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["create", "open", "edit", "delete", "move", "list", "search", "enrich", "get_content", "get_metadata"],
                "required": True
            },
            "path": {
                "type": "string",
                "description": "The path to the note",
                "required": False
            },
            "title": {
                "type": "string",
                "description": "The title for note creation",
                "required": False
            },
            "query": {
                "type": "string",
                "description": "Semantic query for finding notes",
                "required": False
            },
            "content": {
                "type": "string",
                "description": "The content for create/update operations",
                "required": False
            },
            "edits": {
                "type": "object",
                "description": "Edit operations to apply to the note",
                "required": False
            },
            "metadata": {
                "type": "object",
                "description": "Metadata for the note",
                "required": False
            },
            "context": {
                "type": "string",
                "description": "Additional context for semantic operations",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Get the tool manifest for LLM agent.
        
        Returns:
            Dict[str, Any]: Tool manifest with schema and examples
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.inputs,
            "examples": [
                {
                    "action": "open",
                    "query": "User Intent",
                    "context": "Search Results"
                },
                {
                    "action": "edit",
                    "path": "/path/to/file.md",
                    "edits": {"type": "append", "content": "New content to add"}
                },
                {
                    "action": "create",
                    "title": "New Note Title",
                    "content": "Content for the new note"
                },
                {
                    "action": "enrich",
                    "path": "/path/to/file.md",
                    "context": "Additional information to enrich the note"
                }
            ]
        }
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the note management operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        
        try:
            # Initialize services if needed
            if not self.note_manager.is_running:
                await self.note_manager.start()
            if not self.folder_manager.is_running:
                await self.folder_manager.start()
                
            # Execute requested action based on Flow 2 (Semantic Notes Access and Editing)
            if action == "create":
                return await self._create_note(parameters)
            elif action == "open":
                return await self._open_note(parameters)
            elif action == "edit":
                return await self._edit_note(parameters)
            elif action == "delete":
                return await self._delete_note(parameters)
            elif action == "move":
                return await self._move_note(parameters)
            elif action == "list":
                return await self._list_notes()
            elif action == "search":
                return await self._search_notes(parameters)
            elif action == "enrich":
                return await self._enrich_note(parameters)
            elif action == "get_content":
                return await self._get_note_content(parameters)
            elif action == "get_metadata":
                return await self._get_note_metadata(parameters)
            else:
                raise ValueError(f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Note operation failed: {str(e)}")
            raise
            
    async def _create_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new note.
        
        This implements the create action from Flow 2 and Flow 3.
        """
        title = parameters.get("title")
        path = parameters.get("path")
        content = parameters.get("content", "")
        metadata = parameters.get("metadata", {})
        
        if not title and not path:
            raise ValueError("Either title or path is required for create operation")
            
        # If only title is provided, generate a path from it
        if title and not path:
            # Convert title to a safe filename
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
            safe_title = safe_title.replace(" ", "_")
            path = f"{safe_title}.md"
            
        await self.note_manager.create_note(path, content, metadata)
        return {
            "result": {
                "path": path,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "metadata": metadata
            },
            "timestamp": datetime.now().isoformat()
        }
        
    async def _update_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing note."""
        path = parameters.get("path")
        content = parameters.get("content")
        metadata = parameters.get("metadata")
        
        if not path:
            raise ValueError("Path is required for update operation")
            
        if content is not None:
            await self.note_manager.update_content(path, content)
        if metadata is not None:
            await self.note_manager.update_metadata(path, metadata)
            
        return {
            "result": {
                "path": path,
                "success": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
    async def _open_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Open a note with semantic search capability.
        
        This implements the open action from Flow 2.
        It uses both vector and graph databases to find the most relevant notes.
        """
        path = parameters.get("path")
        query = parameters.get("query")
        context = parameters.get("context")
        
        # If path is provided, get the specific note
        if path:
            content = await self.note_manager.get_content(path)
            metadata = await self.note_manager.get_metadata(path)
            
            # Get related notes with both vector and graph search
            related = []
            try:
                # Use semantic search to find related notes using both vector and graph databases
                if self.semantic_analyzer:
                    # This would run the vector and graph searches in parallel as shown in Flow 2
                    related = await self._find_related_notes_with_dual_search(path)
                elif hasattr(self.note_manager, "find_related_notes"):
                    # Fallback to basic related note finding
                    related = await self.note_manager.find_related_notes(path)
            except Exception as e:
                self.logger.warning(f"Failed to find related notes: {str(e)}")
                
            return {
                "result": {
                    "path": path,
                    "content": content,
                    "metadata": metadata,
                    "related": related
                }
            }
            
        # If query is provided, use semantic search
        elif query:
            try:
                # Following Flow 2 - analyze query intent and perform semantic search
                if self.semantic_analyzer and self.embedding_model:
                    # Step 1: Analyze query intent
                    query_intent = await self.semantic_analyzer.analyze_intent(query)
                    
                    # Step 2: Generate query embedding
                    query_vector = await self.embedding_model.generate_embedding(query)
                    
                    # Step 3: Perform parallel vector and graph search
                    vector_results, graph_results = await asyncio.gather(
                        self._vector_search(query_vector),
                        self._graph_search(query_intent)
                    )
                    
                    # Step 4: Merge search results
                    merged_results = await self._merge_search_results(vector_results, graph_results)
                    
                    if not merged_results:
                        return {
                            "result": {
                                "success": False,
                                "message": "No notes found matching the query"
                            }
                        }
                    
                    # Open the first result
                    best_match = merged_results[0]
                    content = await self.note_manager.get_content(best_match["path"])
                    metadata = await self.note_manager.get_metadata(best_match["path"])
                    
                    return {
                        "result": {
                            "path": best_match["path"],
                            "content": content,
                            "metadata": metadata,
                            "related": merged_results[1:5] if len(merged_results) > 1 else []
                        }
                    }
                
                # Fallback to basic search if semantic services aren't available
                search_results = await self.note_manager.search_notes(query)
                
                if not search_results:
                    return {
                        "result": {
                            "success": False,
                            "message": "No notes found matching the query"
                        }
                    }
                    
                # Open the first result
                best_match = search_results[0]
                content = await self.note_manager.get_content(best_match["path"])
                metadata = await self.note_manager.get_metadata(best_match["path"])
                
                return {
                    "result": {
                        "path": best_match["path"],
                        "content": content,
                        "metadata": metadata,
                        "related": search_results[1:5] if len(search_results) > 1 else []
                    }
                }
            except Exception as e:
                self.logger.error(f"Semantic search failed: {str(e)}")
                raise
        else:
            raise ValueError("Either path or query is required for open operation")
    
    async def _find_related_notes_with_dual_search(self, path: str) -> List[Dict[str, Any]]:
        """Find related notes using both vector and graph databases.
        
        Args:
            path: Path to the note
            
        Returns:
            List of related notes with scores and metadata
        """
        # This would be implemented to use both vector and graph databases
        try:
            if not self.vector_db or not self.graph_db or not self.semantic_analyzer:
                return []
                
            # Get note content and generate embedding
            content = await self.note_manager.get_content(path)
            embedding = await self.embedding_model.generate_embedding(content)
            
            # Perform parallel vector and graph searches
            vector_results, graph_results = await asyncio.gather(
                self.vector_db.search_similar(embedding),
                self.graph_db.search_related(path)
            )
            
            # Merge and rank results
            merged_results = await self._merge_search_results(vector_results, graph_results)
            
            return merged_results
        except Exception as e:
            self.logger.error(f"Error finding related notes: {str(e)}")
            return []
    
    async def _vector_search(self, query_vector: List[float]) -> List[Dict[str, Any]]:
        """Search for notes using vector similarity.
        
        Args:
            query_vector: The query embedding vector
            
        Returns:
            List of matching notes with scores
        """
        # This would implement the VectorDB search from Flow 2
        try:
            if not self.vector_db:
                return []
                
            return await self.vector_db.search_similar(query_vector)
        except Exception as e:
            self.logger.error(f"Vector search failed: {str(e)}")
            return []
    
    async def _graph_search(self, query_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for notes using graph relationships.
        
        Args:
            query_intent: Analyzed query intent
            
        Returns:
            List of matching notes with scores
        """
        # This would implement the GraphDB search from Flow 2
        try:
            if not self.graph_db:
                return []
                
            return await self.graph_db.search_relationships(query_intent)
        except Exception as e:
            self.logger.error(f"Graph search failed: {str(e)}")
            return []
    
    async def _merge_search_results(
        self, 
        vector_results: List[Dict[str, Any]], 
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge results from vector and graph searches.
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            
        Returns:
            Merged and ranked results
        """
        # This would implement the results merging from Flow 2
        try:
            # Create a unified results dictionary
            merged_dict = {}
            
            # Add vector results
            for result in vector_results:
                path = result["path"]
                score = result["score"]
                
                if path in merged_dict:
                    merged_dict[path]["vector_score"] = score
                    merged_dict[path]["combined_score"] += score * 0.6  # Weight vector results at 60%
                else:
                    merged_dict[path] = {
                        "path": path,
                        "vector_score": score,
                        "graph_score": 0,
                        "combined_score": score * 0.6
                    }
            
            # Add graph results
            for result in graph_results:
                path = result["path"]
                score = result["score"]
                
                if path in merged_dict:
                    merged_dict[path]["graph_score"] = score
                    merged_dict[path]["combined_score"] += score * 0.4  # Weight graph results at 40%
                else:
                    merged_dict[path] = {
                        "path": path,
                        "vector_score": 0,
                        "graph_score": score,
                        "combined_score": score * 0.4
                    }
            
            # Convert to list and sort by combined score
            merged_results = list(merged_dict.values())
            merged_results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            return merged_results
        except Exception as e:
            self.logger.error(f"Error merging search results: {str(e)}")
            return []
    
    async def _edit_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a note with semantic awareness.
        
        This implements the edit action from Flow 2.
        Includes analysis of edit impact and updates to both vector and graph indices.
        """
        path = parameters.get("path")
        edits = parameters.get("edits")
        content = parameters.get("content")
        metadata = parameters.get("metadata")
        
        if not path:
            raise ValueError("Path is required for edit operation")
            
        updates = {
            "vector": False,
            "graph": False
        }
        
        try:
            # Get the original content for later analysis
            original_content = await self.note_manager.get_content(path)
            original_metadata = await self.note_manager.get_metadata(path)
            
            # Apply content update if provided
            new_content = original_content
            if content is not None:
                await self.note_manager.update_content(path, content)
                new_content = content
                updates["vector"] = True
                
            # Apply edits if provided
            elif edits is not None:
                # Apply the edits based on edit type
                edit_type = edits.get("type", "replace")
                if edit_type == "replace":
                    # Replace entire content or section
                    new_content = edits.get("content", "")
                    section = edits.get("section")
                    
                    if section:
                        # Replace only a section
                        # Implementation depends on section detection logic
                        raise NotImplementedError("Section replacement not yet implemented")
                    else:
                        # Replace entire content
                        await self.note_manager.update_content(path, new_content)
                        
                elif edit_type == "append":
                    # Append to the end of the note
                    append_content = edits.get("content", "")
                    new_content = original_content + "\n\n" + append_content
                    await self.note_manager.update_content(path, new_content)
                    
                elif edit_type == "prepend":
                    # Prepend to the beginning of the note
                    prepend_content = edits.get("content", "")
                    new_content = prepend_content + "\n\n" + original_content
                    await self.note_manager.update_content(path, new_content)
                    
                elif edit_type == "insert":
                    # Insert at a specific position
                    insert_content = edits.get("content", "")
                    position = edits.get("position", 0)
                    
                    new_content = original_content[:position] + insert_content + original_content[position:]
                    await self.note_manager.update_content(path, new_content)
                    
                updates["vector"] = True
                
            # Apply metadata update if provided
            new_metadata = original_metadata
            if metadata is not None:
                await self.note_manager.update_metadata(path, metadata)
                new_metadata = metadata
                updates["graph"] = True
                
            # Analyze edit impact using SemanticAnalyzer
            if self.semantic_analyzer and (updates["vector"] or updates["graph"]):
                try:
                    # Generate edit embedding
                    if self.embedding_model and updates["vector"]:
                        # Generate embeddings for the content changes
                        edit_embedding = await self.embedding_model.generate_embedding(new_content)
                        
                        # Update vector index with new embedding
                        if self.vector_db:
                            await self.vector_db.update_vector(path, edit_embedding)
                            self.logger.info(f"Updated vector index for {path}")
                    
                    # Update knowledge graph with new metadata and relationships
                    if self.graph_db and (updates["vector"] or updates["graph"]):
                        # Analyze content impact on graph
                        edit_analysis = await self.semantic_analyzer.analyze_edit_impact(
                            original_content, 
                            new_content,
                            original_metadata,
                            new_metadata
                        )
                        
                        # Update the knowledge graph
                        await self.graph_db.update_knowledge_graph(path, edit_analysis)
                        self.logger.info(f"Updated graph index for {path}")
                        
                    updates["vector"] = True
                    updates["graph"] = True
                    
                except Exception as e:
                    self.logger.error(f"Index update failed: {str(e)}")
                    # Continue execution even if index update fails
                    # The main content update already succeeded
                
            return {
                "result": {
                    "success": True,
                    "updates": updates,
                    "path": path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Edit failed: {str(e)}")
            raise
            
    async def _enrich_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a note with additional content or context.
        
        This implements the enrich action from Flow 3.
        """
        path = parameters.get("path")
        context = parameters.get("context")
        
        if not path or not context:
            raise ValueError("Path and context are required for enrich operation")
            
        try:
            # Get current content
            current_content = await self.note_manager.get_content(path)
            
            # Append the enrichment content
            enriched_content = current_content + "\n\n## Additional Information\n\n" + context
            
            # Update the note
            await self.note_manager.update_content(path, enriched_content)
            
            return {
                "result": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Enrichment failed: {str(e)}")
            raise
        
    async def _delete_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for delete operation")
            
        await self.note_manager.delete_note(path)
        return {
            "message": f"Deleted note at {path}",
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _move_note(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Move a note to a new location."""
        path = parameters.get("path")
        new_path = parameters.get("new_path")
        
        if not path or not new_path:
            raise ValueError("Path and new_path are required for move operation")
            
        await self.note_manager.move_note(path, new_path)
        return {
            "message": f"Moved note from {path} to {new_path}",
            "old_path": path,
            "new_path": new_path,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _list_notes(self) -> Dict[str, Any]:
        """List all notes in the vault."""
        notes = await self.note_manager.list_notes()
        return {
            "notes": notes,
            "count": len(notes),
            "timestamp": datetime.now().isoformat()
        }
        
    async def _search_notes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for notes matching a query."""
        query = parameters.get("search_query")
        if not query:
            raise ValueError("Search query is required for search operation")
            
        results = await self.note_manager.search_notes(query)
        return {
            "results": results,
            "count": len(results),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_note_content(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get the content of a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for get_content operation")
            
        content = await self.note_manager.get_content(path)
        return {
            "path": path,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _get_note_metadata(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get the metadata of a note."""
        path = parameters.get("path")
        if not path:
            raise ValueError("Path is required for get_metadata operation")
            
        metadata = await self.note_manager.get_metadata(path)
        return {
            "path": path,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

class ListNotesTool(BaseTool):
    """Tool for listing notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the list notes tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "list_notes"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "List notes in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "folder": {
                "type": "string",
                "description": "The folder to list notes from",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the list notes operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        folder = parameters.get("folder")
        
        try:
            notes = await self.note_manager.list_notes(folder)
            return {
                "notes": notes,
                "count": len(notes),
                "folder": folder or "root",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to list notes: {str(e)}")
            raise

class SearchNotesTool(BaseTool):
    """Tool for searching notes in the Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """Initialize the search notes tool."""
        super().__init__()
        self.vault_path = vault_path
        self.note_manager = NoteManager(vault_path)
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "search_notes"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Search for notes in the Obsidian vault"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "query": {
                "type": "string",
                "description": "The search query",
                "required": True
            },
            "folder": {
                "type": "string",
                "description": "The folder to search in",
                "required": False
            }
        }
        
    @property
    def output_type(self) -> str:
        """Get the tool output type."""
        return "object"
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the search notes operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        query = parameters["query"]
        folder = parameters.get("folder")
        
        try:
            results = await self.note_manager.search_notes(query, folder)
            return {
                "results": results,
                "count": len(results),
                "query": query,
                "folder": folder or "root",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to search notes: {str(e)}")
            raise 
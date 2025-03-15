from typing import Dict, Any, List, Optional
from ..core.tool_interfaces import TextToolInterface
from ..core.exceptions import TextProcessingError
from ..services.text_processing import TextProcessor
from .base_tools import BaseTool
from pathlib import Path
from datetime import datetime

class ChunkTextTool(TextToolInterface):
    """Tool for chunking text content."""
    name = "chunk_text"
    description = "Split text into semantic chunks"
    
    async def forward(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> Dict[str, Any]:
        """Split text into semantic chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            Dictionary containing chunked text
        """
        return await self.chunk_text(text, chunk_size, overlap)

class ExtractEntitiesTool(TextToolInterface):
    """Tool for extracting entities from text."""
    name = "extract_entities"
    description = "Extract named entities from text"
    
    async def forward(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Extract named entities from text.
        
        Args:
            text: Text to analyze
            entity_types: Optional list of entity types to extract
            
        Returns:
            Dictionary containing extracted entities
        """
        return await self.extract_entities(text, entity_types)

class SummarizeTextTool(TextToolInterface):
    """Tool for summarizing text content."""
    name = "summarize_text"
    description = "Generate a summary of text content"
    
    async def forward(
        self,
        text: str,
        max_length: int = 200,
        min_length: int = 50
    ) -> Dict[str, Any]:
        """Generate a summary of text content.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Dictionary containing text summary
        """
        return await self.summarize_text(text, max_length, min_length)

class AnalyzeSentimentTool(TextToolInterface):
    """Tool for analyzing text sentiment."""
    name = "analyze_sentiment"
    description = "Analyze sentiment of text content"
    
    async def forward(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Analyze sentiment of text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis
        """
        return await self.analyze_sentiment(text)

class ContentTool(BaseTool):
    """Tool for content processing operations.
    
    This implements the ContentTool functionality from Flow 8.
    """
    
    def __init__(self, content_processor):
        """Initialize the content tool.
        
        Args:
            content_processor: Content processor instance
        """
        super().__init__()
        self.content_processor = content_processor
        
    @property
    def name(self) -> str:
        """Get the tool name."""
        return "ContentTool"
        
    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Process note content for summarization, proofreading, and other text operations"
        
    @property
    def inputs(self) -> Dict[str, Any]:
        """Get the tool input schema."""
        return {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": ["summarize", "proofread", "format", "analyze", "extract_entities"],
                "required": True
            },
            "content": {
                "type": "string",
                "description": "The content to process",
                "required": False
            },
            "path": {
                "type": "string",
                "description": "Path to the note to process",
                "required": False
            },
            "options": {
                "type": "object",
                "description": "Additional options for processing",
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
                    "action": "summarize",
                    "path": "/path/to/note.md",
                    "options": {"max_length": 200}
                },
                {
                    "action": "proofread",
                    "content": "This is a draft document with some erors that need to be fixed.",
                    "options": {"fix_spelling": True, "improve_grammar": True}
                },
                {
                    "action": "extract_entities",
                    "content": "Meeting with John Smith on June 15th about the new project.",
                    "options": {"entity_types": ["PERSON", "DATE", "ORG"]}
                }
            ]
        }
        
    async def _execute_tool(self, parameters: Dict[str, Any]) -> Any:
        """Execute the content processing operation.
        
        Args:
            parameters (Dict[str, Any]): The validated parameters
            
        Returns:
            Any: The operation result
            
        Raises:
            ToolError: If the operation fails
        """
        action = parameters["action"]
        content = parameters.get("content")
        path = parameters.get("path")
        options = parameters.get("options", {})
        
        # Get content from path if provided
        if not content and path:
            content = await self._get_note_content(path)
            
        if not content:
            raise ValueError("Either content or path must be provided")
            
        try:
            # This follows the Flow 8 (Content Processing Flow)
            if action == "summarize":
                return await self._summarize_content(content, options)
            elif action == "proofread":
                return await self._proofread_content(content, options, path)
            elif action == "format":
                return await self._format_content(content, options, path)
            elif action == "analyze":
                return await self._analyze_content(content, options)
            elif action == "extract_entities":
                return await self._extract_entities(content, options)
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            self.logger.error(f"Content processing failed: {str(e)}")
            raise
            
    async def _summarize_content(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize content.
        
        This corresponds to the Summarize action in Flow 8.
        """
        max_length = options.get("max_length", 200)
        min_length = options.get("min_length", 50)
        
        try:
            summary = await self.content_processor.summarize(
                content=content,
                max_length=max_length,
                min_length=min_length
            )
            
            return {
                "summary": summary
            }
        except Exception as e:
            raise TextProcessingError(f"Summarization failed: {str(e)}")
            
    async def _proofread_content(self, content: str, options: Dict[str, Any], path: Optional[str] = None) -> Dict[str, Any]:
        """Proofread content.
        
        This corresponds to the Proofread action in Flow 8.
        """
        fix_spelling = options.get("fix_spelling", True)
        improve_grammar = options.get("improve_grammar", True)
        improve_clarity = options.get("improve_clarity", False)
        
        try:
            proofread_content = await self.content_processor.proofread(
                content=content,
                fix_spelling=fix_spelling,
                improve_grammar=improve_grammar,
                improve_clarity=improve_clarity
            )
            
            # Update note if path provided
            if path:
                await self._update_note_content(path, proofread_content)
                
            return {
                "proofread_content": proofread_content
            }
        except Exception as e:
            raise TextProcessingError(f"Proofreading failed: {str(e)}")
            
    async def _format_content(self, content: str, options: Dict[str, Any], path: Optional[str] = None) -> Dict[str, Any]:
        """Format content.
        
        This corresponds to formatting operations in Flow 8.
        """
        format_type = options.get("format", "markdown")
        
        try:
            formatted_content = await self.content_processor.format(
                content=content,
                format_type=format_type
            )
            
            # Update note if path provided
            if path:
                await self._update_note_content(path, formatted_content)
                
            return {
                "formatted_content": formatted_content
            }
        except Exception as e:
            raise TextProcessingError(f"Formatting failed: {str(e)}")
            
    async def _analyze_content(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content.
        
        This corresponds to analysis operations in Flow 8.
        """
        analysis_type = options.get("type", "general")
        
        try:
            analysis = await self.content_processor.analyze(
                content=content,
                analysis_type=analysis_type
            )
            
            return {
                "analysis": analysis
            }
        except Exception as e:
            raise TextProcessingError(f"Analysis failed: {str(e)}")
            
    async def _extract_entities(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from content.
        
        This corresponds to entity extraction operations in Flow 8.
        """
        entity_types = options.get("entity_types", ["PERSON", "ORG", "DATE", "LOC"])
        
        try:
            entities = await self.content_processor.extract_entities(
                content=content,
                entity_types=entity_types
            )
            
            return {
                "entities": entities
            }
        except Exception as e:
            raise TextProcessingError(f"Entity extraction failed: {str(e)}")
            
    async def _get_note_content(self, path: str) -> str:
        """Helper method to get note content."""
        note_path = Path(path)
        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")
            
        return note_path.read_text()
        
    async def _update_note_content(self, path: str, content: str) -> None:
        """Helper method to update note content."""
        note_path = Path(path)
        if not note_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")
            
        note_path.write_text(content) 
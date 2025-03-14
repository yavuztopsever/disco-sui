from typing import Dict, Any, List, Optional
from ..core.tool_interfaces import TextToolInterface
from ..core.exceptions import TextProcessingError
from ..services.text_processing import TextProcessor

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
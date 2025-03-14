from typing import List, Dict, Any
import numpy as np
from pydantic import BaseModel

class ChunkingConfig(BaseModel):
    """Configuration for text chunking."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    respect_boundaries: bool = True  # Whether to respect markdown boundaries
    include_metadata: bool = True

class TextProcessor:
    """Unified text processing service."""
    
    @staticmethod
    def chunk_content(
        content: str,
        config: ChunkingConfig = ChunkingConfig()
    ) -> List[Dict[str, Any]]:
        """Split content into chunks with configurable parameters.
        
        Args:
            content: Text content to chunk
            config: Chunking configuration
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        if config.respect_boundaries:
            # Split on markdown headings and paragraphs
            sections = TextProcessor._split_on_boundaries(content)
            for section in sections:
                section_chunks = TextProcessor._chunk_section(
                    section,
                    config.chunk_size,
                    config.chunk_overlap
                )
                chunks.extend(section_chunks)
        else:
            # Simple word-based chunking
            words = content.split()
            current_chunk = []
            current_size = 0
            
            for word in words:
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space
                
                if current_size >= config.chunk_size:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(TextProcessor._create_chunk_dict(chunk_text))
                    
                    # Keep overlap words for next chunk
                    overlap_words = current_chunk[-config.chunk_overlap:]
                    current_chunk = overlap_words
                    current_size = sum(len(word) + 1 for word in overlap_words)
            
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(TextProcessor._create_chunk_dict(chunk_text))
        
        return chunks

    @staticmethod
    def _split_on_boundaries(content: str) -> List[str]:
        """Split content on markdown boundaries."""
        import re
        # Split on headings and double newlines
        pattern = r'(#{1,6}\s.*?(?:\n|$)|\n\n)'
        sections = re.split(pattern, content)
        # Filter out empty sections and clean
        return [s.strip() for s in sections if s and s.strip()]

    @staticmethod
    def _chunk_section(
        section: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Chunk a single section of text."""
        words = section.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunk_text = " ".join(current_chunk)
                chunks.append(TextProcessor._create_chunk_dict(chunk_text))
                
                overlap_words = current_chunk[-chunk_overlap:]
                current_chunk = overlap_words
                current_size = sum(len(word) + 1 for word in overlap_words)
        
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(TextProcessor._create_chunk_dict(chunk_text))
        
        return chunks

    @staticmethod
    def _create_chunk_dict(text: str) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata."""
        return {
            "text": text,
            "char_length": len(text),
            "word_count": len(text.split()),
            "metadata": {}  # Can be extended with additional metadata
        }

    @staticmethod
    def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) 
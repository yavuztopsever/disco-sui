"""Semantic analysis implementation."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

from ...core.exceptions import SemanticAnalysisError
from ..base_service import BaseService


class SemanticAnalyzer(BaseService):
    """Service for semantic analysis of content."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the semantic analyzer.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        super().__init__()
        self.model_name = model_name
        self._model = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the semantic analyzer.
        
        Raises:
            SemanticAnalysisError: If initialization fails
        """
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._initialized = True
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to initialize semantic analyzer: {str(e)}")
    
    async def encode_text(self, text: str) -> np.ndarray:
        """Encode text into a semantic vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Semantic vector representation
            
        Raises:
            SemanticAnalysisError: If encoding fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return self._model.encode(text)
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to encode text: {str(e)}")
    
    async def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Encode multiple texts into semantic vectors.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Array of semantic vectors
            
        Raises:
            SemanticAnalysisError: If encoding fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return self._model.encode(texts)
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to encode batch: {str(e)}")
    
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
            
        Raises:
            SemanticAnalysisError: If similarity computation fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            vec1 = await self.encode_text(text1)
            vec2 = await self.encode_text(text2)
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to compute similarity: {str(e)}")
    
    async def find_similar_texts(
        self,
        query: str,
        texts: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find most similar texts to a query.
        
        Args:
            query: Query text
            texts: List of texts to search
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing text and similarity score
            
        Raises:
            SemanticAnalysisError: If search fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            query_vec = await self.encode_text(query)
            text_vecs = await self.encode_batch(texts)
            
            similarities = np.dot(text_vecs, query_vec) / (
                np.linalg.norm(text_vecs, axis=1) * np.linalg.norm(query_vec)
            )
            
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            return [
                {
                    "text": texts[i],
                    "similarity": float(similarities[i])
                }
                for i in top_indices
            ]
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to find similar texts: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._model = None
        self._initialized = False 
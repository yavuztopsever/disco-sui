from typing import Dict, Any, List, Optional
from pathlib import Path
from ..core.tool_interfaces import SemanticToolInterface, AnalysisTool
from ..core.exceptions import SemanticAnalysisError
from ..services.semantic_analysis import SemanticAnalyzer
from .base_tools import BaseTool
import os
import json
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import spacy
from collections import defaultdict
from ..core.tool_interfaces import ToolResponse

class SemanticAnalysisTool(AnalysisTool):
    """Tool for semantic analysis of content."""
    
    async def forward(
        self,
        content: str,
        analysis_type: str = "semantic",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content semantically.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis to perform
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        return await self.analyze_content(content, analysis_type, **kwargs)

class RelatedContentTool(AnalysisTool):
    """Tool for finding related content."""
    
    async def forward(
        self,
        source: str,
        max_results: int = 5,
        min_similarity: float = 0.5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Find content related to source.
        
        Args:
            source: Source content
            max_results: Maximum number of results
            min_similarity: Minimum similarity threshold
            **kwargs: Additional search parameters
            
        Returns:
            List of related items
        """
        return await self.find_related(source, max_results, min_similarity, **kwargs)

class KnowledgeGraphTool(AnalysisTool):
    """Tool for generating knowledge graphs."""
    
    async def forward(
        self,
        include_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate knowledge graph.
        
        Args:
            include_types: Types of relationships to include
            **kwargs: Additional graph parameters
            
        Returns:
            Graph data
        """
        return await self.generate_graph(include_types, **kwargs)

class AnalyzeRelationshipsTool(SemanticToolInterface):
    """Tool for analyzing relationships between notes."""
    name = "analyze_relationships"
    description = "Analyze relationships between notes"
    
    async def forward(
        self,
        note_paths: List[str],
        analysis_type: str = "semantic"
    ) -> Dict[str, Any]:
        """Analyze relationships between notes.
        
        Args:
            note_paths: List of note paths to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary containing relationship analysis
        """
        try:
            results = []
            for path in note_paths:
                # Analyze each note
                analysis = await self.semantic_analyzer.analyze_note(Path(path))
                results.append(analysis)
            
            # Find relationships between notes
            relationships = []
            for i, note1 in enumerate(note_paths):
                for note2 in note_paths[i+1:]:
                    # Get shared entities and calculate similarity
                    shared = await self._find_shared_entities(note1, note2)
                    if shared:
                        relationships.append({
                            "source": note1,
                            "target": note2,
                            "shared_entities": shared
                        })
            
            return {
                "success": True,
                "analyses": results,
                "relationships": relationships
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _find_shared_entities(
        self,
        note1: str,
        note2: str
    ) -> List[Dict[str, str]]:
        """Find entities shared between two notes."""
        try:
            # Get entities for both notes
            entities1 = await self.semantic_analyzer._extract_entities(
                await self.semantic_analyzer._read_note(Path(note1))
            )
            entities2 = await self.semantic_analyzer._extract_entities(
                await self.semantic_analyzer._read_note(Path(note2))
            )
            
            # Find shared entities
            shared = []
            entities1_set = {(e["text"], e["type"]) for e in entities1}
            entities2_set = {(e["text"], e["type"]) for e in entities2}
            
            for text, type_ in entities1_set & entities2_set:
                shared.append({
                    "text": text,
                    "type": type_
                })
            
            return shared
            
        except Exception as e:
            raise SemanticAnalysisError(f"Error finding shared entities: {str(e)}")

class FindRelatedNotesTool(SemanticToolInterface):
    """Tool for finding related notes."""
    name = "find_related_notes"
    description = "Find notes related to a given note"
    
    async def forward(
        self,
        note_path: str,
        max_related: int = 5,
        min_similarity: float = 0.5
    ) -> Dict[str, Any]:
        """Find notes related to a given note.
        
        Args:
            note_path: Path to the note
            max_related: Maximum number of related notes to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Dictionary containing related notes
        """
        return await self.find_related_notes(note_path, max_related, min_similarity)

class GenerateKnowledgeGraphTool(SemanticToolInterface):
    """Tool for generating knowledge graphs."""
    name = "generate_knowledge_graph"
    description = "Generate a knowledge graph of the vault"
    
    async def forward(
        self,
        include_hierarchy: bool = True,
        include_semantic: bool = True
    ) -> Dict[str, Any]:
        """Generate a knowledge graph.
        
        Args:
            include_hierarchy: Whether to include hierarchical relationships
            include_semantic: Whether to include semantic relationships
            
        Returns:
            Dictionary containing graph data
        """
        return await self.generate_knowledge_graph(include_hierarchy, include_semantic)

class AnalyzeNoteTool(SemanticToolInterface):
    """Tool for analyzing note content."""
    name = "analyze_note"
    description = "Perform semantic analysis on a note"
    
    async def forward(self, note_path: str) -> Dict[str, Any]:
        """Analyze a note's content.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Dictionary containing analysis results
        """
        return await self.analyze_note(note_path) 
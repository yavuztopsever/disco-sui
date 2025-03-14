from typing import List, Dict, Any, Optional
import networkx as nx
from pathlib import Path
from pydantic import BaseModel
from .text_processing import TextProcessor
from .exceptions import SemanticAnalysisError

class EntityOccurrence(BaseModel):
    """Model for entity occurrence in a note."""
    text: str
    type: str
    note_path: str
    context: str

class RelationshipType(BaseModel):
    """Model for relationship between notes."""
    source: str
    target: str
    type: str
    strength: float
    context: str

class SemanticAnalyzer:
    """Unified service for semantic analysis operations."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.text_processor = TextProcessor()
        self.entity_index: Dict[str, List[EntityOccurrence]] = {}
        self.relationship_graph = nx.Graph()
        self.semantic_graph = nx.Graph()
        self.hierarchy_graph = nx.Graph()

    async def analyze_note(self, note_path: Path) -> Dict[str, Any]:
        """Perform comprehensive semantic analysis of a note.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            content = await self._read_note(note_path)
            
            # Extract entities
            entities = await self._extract_entities(content)
            
            # Update entity index
            self._update_entity_index(note_path, entities)
            
            # Analyze relationships
            relationships = await self._analyze_relationships(note_path, content)
            
            # Update graphs
            self._update_graphs(note_path, entities, relationships)
            
            return {
                "success": True,
                "note_path": str(note_path),
                "entities": entities,
                "relationships": relationships
            }
            
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to analyze note: {str(e)}")

    async def find_related_notes(
        self,
        note_path: Path,
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
        try:
            # Get direct connections from semantic graph
            if note_path not in self.semantic_graph:
                return {"success": True, "related_notes": []}
            
            neighbors = list(self.semantic_graph.neighbors(note_path))
            neighbor_data = []
            
            for neighbor in neighbors:
                similarity = self.semantic_graph[note_path][neighbor]["weight"]
                if similarity >= min_similarity:
                    neighbor_data.append({
                        "path": str(neighbor),
                        "similarity": similarity,
                        "relationship_type": self.semantic_graph[note_path][neighbor].get("type", "semantic")
                    })
            
            # Sort by similarity
            neighbor_data.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "success": True,
                "related_notes": neighbor_data[:max_related]
            }
            
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to find related notes: {str(e)}")

    async def generate_knowledge_graph(
        self,
        include_hierarchy: bool = True,
        include_semantic: bool = True
    ) -> Dict[str, Any]:
        """Generate a knowledge graph of the vault.
        
        Args:
            include_hierarchy: Whether to include hierarchical relationships
            include_semantic: Whether to include semantic relationships
            
        Returns:
            Dictionary containing graph data
        """
        try:
            merged_graph = nx.Graph()
            
            if include_hierarchy:
                merged_graph.add_edges_from(self.hierarchy_graph.edges(data=True))
            
            if include_semantic:
                for edge in self.semantic_graph.edges(data=True):
                    source, target, data = edge
                    if merged_graph.has_edge(source, target):
                        # Combine relationship data
                        existing_data = merged_graph[source][target]
                        merged_data = {
                            "weight": max(existing_data["weight"], data["weight"]),
                            "types": list(set(existing_data.get("types", []) + [data.get("type", "semantic")]))
                        }
                        merged_graph[source][target].update(merged_data)
                    else:
                        merged_graph.add_edge(source, target, **data)
            
            # Convert to serializable format
            nodes = [{"id": str(n), "type": "note"} for n in merged_graph.nodes()]
            edges = [{
                "source": str(s),
                "target": str(t),
                "weight": d.get("weight", 1.0),
                "types": d.get("types", [d.get("type", "semantic")])
            } for s, t, d in merged_graph.edges(data=True)]
            
            return {
                "success": True,
                "graph": {
                    "nodes": nodes,
                    "edges": edges
                }
            }
            
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to generate knowledge graph: {str(e)}")

    async def _read_note(self, path: Path) -> str:
        """Read a note's content."""
        try:
            return path.read_text()
        except Exception as e:
            raise SemanticAnalysisError(f"Failed to read note {path}: {str(e)}")

    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content."""
        # This would use LLM to extract entities
        # Placeholder implementation
        return []

    def _update_entity_index(
        self,
        note_path: Path,
        entities: List[Dict[str, Any]]
    ) -> None:
        """Update the entity index with new entities."""
        for entity in entities:
            if entity["text"] not in self.entity_index:
                self.entity_index[entity["text"]] = []
            self.entity_index[entity["text"]].append(
                EntityOccurrence(
                    text=entity["text"],
                    type=entity["type"],
                    note_path=str(note_path),
                    context=entity.get("context", "")
                )
            )

    async def _analyze_relationships(
        self,
        note_path: Path,
        content: str
    ) -> List[RelationshipType]:
        """Analyze relationships between notes."""
        # This would use LLM to analyze relationships
        # Placeholder implementation
        return []

    def _update_graphs(
        self,
        note_path: Path,
        entities: List[Dict[str, Any]],
        relationships: List[RelationshipType]
    ) -> None:
        """Update the knowledge graphs with new information."""
        # Update semantic graph
        for rel in relationships:
            self.semantic_graph.add_edge(
                rel.source,
                rel.target,
                weight=rel.strength,
                type=rel.type
            )
        
        # Update hierarchy graph based on file system structure
        parent = note_path.parent
        if parent != self.vault_path:
            self.hierarchy_graph.add_edge(
                str(parent),
                str(note_path),
                type="contains"
            ) 
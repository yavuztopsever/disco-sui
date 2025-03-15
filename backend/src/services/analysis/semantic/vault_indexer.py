from typing import Dict, List, Optional, Set, Union, Any
from pathlib import Path
from datetime import datetime
from ...core.exceptions import IndexingError
from ...core.config import settings
from .indexer import Indexer
from ..semantic_analysis.knowledge_graph import KnowledgeGraph, HierarchyNode
from ..note_management.note_manager import NoteManager

class VaultIndexer:
    def __init__(self):
        self.indexer = Indexer()
        self.knowledge_graph = KnowledgeGraph()
        self.note_manager = NoteManager()
        self.vault_path = Path(settings.VAULT_PATH)

    def index_vault(self) -> Dict[str, Any]:
        """Index the entire vault and create knowledge graph."""
        try:
            results = {
                "indexed_notes": [],
                "created_nodes": [],
                "issues": []
            }

            # First, index all notes for semantic search
            index_results = self.indexer.index_directory(str(self.vault_path))
            results["indexed_notes"] = list(index_results.keys())

            # Then, analyze notes and create knowledge graph
            for note_path in self.vault_path.glob("**/*.md"):
                try:
                    note_title = note_path.stem
                    metadata = self.note_manager.get_note_metadata(note_title)
                    
                    # Create hierarchy node
                    node = HierarchyNode(
                        title=note_title,
                        type=metadata.type,
                        parent=metadata.parent_node,
                        children=metadata.related_nodes,
                        metadata={
                            "path": str(note_path),
                            "tags": metadata.tags,
                            "created_at": metadata.created_at,
                            "updated_at": metadata.updated_at
                        }
                    )
                    
                    # Add to knowledge graph
                    self.knowledge_graph.add_node_to_hierarchy(node)
                    results["created_nodes"].append(note_title)
                    
                except Exception as e:
                    results["issues"].append({
                        "note": note_title,
                        "error": str(e)
                    })

            # Validate hierarchy
            validation_issues = self.knowledge_graph.validate_hierarchy()
            results["issues"].extend(validation_issues)

            return results
        except Exception as e:
            raise IndexingError(f"Error indexing vault: {str(e)}")

    def update_note_index(self, note_title: str) -> Dict[str, Any]:
        """Update index and knowledge graph for a single note."""
        try:
            results = {
                "indexed": False,
                "node_updated": False,
                "issues": []
            }

            # Update semantic index
            self.indexer.update_index(note_title)
            results["indexed"] = True

            # Update knowledge graph
            metadata = self.note_manager.get_note_metadata(note_title)
            node = HierarchyNode(
                title=note_title,
                type=metadata.type,
                parent=metadata.parent_node,
                children=metadata.related_nodes,
                metadata={
                    "path": str(self.vault_path / f"{note_title}.md"),
                    "tags": metadata.tags,
                    "created_at": metadata.created_at,
                    "updated_at": metadata.updated_at
                }
            )
            
            self.knowledge_graph.add_node_to_hierarchy(node)
            results["node_updated"] = True

            return results
        except Exception as e:
            raise IndexingError(f"Error updating note index: {str(e)}")

    def get_note_hierarchy(self, note_title: str) -> Dict[str, Any]:
        """Get the complete hierarchy for a note."""
        try:
            return self.knowledge_graph.get_node_hierarchy(note_title)
        except Exception as e:
            raise IndexingError(f"Error getting note hierarchy: {str(e)}")

    def get_note_relationships(self, note_title: str) -> Dict[str, List[str]]:
        """Get all relationships for a note."""
        try:
            return self.knowledge_graph.analyze_node_relationships(note_title)
        except Exception as e:
            raise IndexingError(f"Error getting note relationships: {str(e)}")

    def get_connection_suggestions(self, note_title: str) -> List[Dict[str, Any]]:
        """Get suggestions for potential connections."""
        try:
            return self.knowledge_graph.suggest_node_connections(note_title)
        except Exception as e:
            raise IndexingError(f"Error getting connection suggestions: {str(e)}")

    def get_merged_graph(self) -> Dict[str, Any]:
        """Get the merged semantic and hierarchy graph."""
        try:
            merged_graph = self.knowledge_graph.merge_semantic_and_hierarchy()
            
            # Convert to serializable format
            graph_data = {
                "nodes": [],
                "edges": []
            }
            
            for node in merged_graph.nodes():
                node_data = merged_graph.nodes[node]
                graph_data["nodes"].append({
                    "id": node,
                    "type": node_data.get("type"),
                    "metadata": node_data.get("metadata", {})
                })
            
            for edge in merged_graph.edges():
                edge_data = merged_graph.edges[edge]
                graph_data["edges"].append({
                    "source": edge[0],
                    "target": edge[1],
                    "relationship": edge_data.get("relationship")
                })
            
            return graph_data
        except Exception as e:
            raise IndexingError(f"Error getting merged graph: {str(e)}")

    def find_orphaned_notes(self) -> List[str]:
        """Find notes that are not connected to any parent."""
        try:
            return self.knowledge_graph.find_orphaned_nodes()
        except Exception as e:
            raise IndexingError(f"Error finding orphaned notes: {str(e)}")

    def get_vault_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vault's structure."""
        try:
            stats = {
                "total_notes": 0,
                "notes_by_type": {},
                "orphaned_notes": 0,
                "hierarchy_depth": 0,
                "semantic_connections": 0
            }

            # Count notes and types
            for node in self.knowledge_graph.hierarchy_graph.nodes():
                stats["total_notes"] += 1
                node_type = self.knowledge_graph.hierarchy_graph.nodes[node]["type"]
                stats["notes_by_type"][node_type] = stats["notes_by_type"].get(node_type, 0) + 1

            # Count orphaned notes
            stats["orphaned_notes"] = len(self.find_orphaned_notes())

            # Calculate hierarchy depth
            def get_depth(node: str, visited: set) -> int:
                if node in visited:
                    return 0
                visited.add(node)
                max_child_depth = 0
                for child in self.knowledge_graph.hierarchy_graph.successors(node):
                    child_depth = get_depth(child, visited)
                    max_child_depth = max(max_child_depth, child_depth)
                return 1 + max_child_depth

            visited = set()
            root_nodes = [node for node in self.knowledge_graph.hierarchy_graph.nodes()
                         if not any(self.knowledge_graph.hierarchy_graph.has_edge(parent, node)
                                  for parent in self.knowledge_graph.hierarchy_graph.nodes())]
            
            for root in root_nodes:
                stats["hierarchy_depth"] = max(stats["hierarchy_depth"], get_depth(root, visited))

            # Count semantic connections
            stats["semantic_connections"] = len(self.knowledge_graph.semantic_graph.edges())

            return stats
        except Exception as e:
            raise IndexingError(f"Error getting vault statistics: {str(e)}") 
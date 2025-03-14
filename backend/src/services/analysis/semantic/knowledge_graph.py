from typing import Dict, List, Optional, Set
from pydantic import BaseModel
import networkx as nx
from ...core.exceptions import GraphError
from ...features.note_management.note_manager import NoteManager
from .semantic_analyzer import SemanticNode, SemanticGraph

class HierarchyNode(BaseModel):
    """Model for hierarchy nodes."""
    title: str
    type: str  # e.g., "Person", "Category", "Main", "Document", "Note", "Log", "Code", "Mail"
    parent: Optional[str]
    children: List[str]
    metadata: Dict[str, any]

class KnowledgeGraph:
    def __init__(self):
        self.note_manager = NoteManager()
        self.semantic_analyzer = SemanticAnalyzer()
        self.hierarchy_graph = nx.DiGraph()  # Directed graph for hierarchy
        self.semantic_graph = nx.Graph()     # Undirected graph for semantic relationships
        self.node_types = {
            "Person": 0,
            "Category": 1,
            "Main": 2,
            "Document": 3,
            "Note": 3,
            "Log": 3,
            "Code": 3,
            "Mail": 3
        }

    def add_node_to_hierarchy(self, node: HierarchyNode) -> None:
        """Add a node to the hierarchy graph."""
        try:
            # Add node with its metadata
            self.hierarchy_graph.add_node(
                node.title,
                type=node.type,
                metadata=node.metadata
            )

            # Add edge from parent if exists
            if node.parent:
                if node.parent not in self.hierarchy_graph:
                    raise GraphError(f"Parent node {node.parent} does not exist")
                self.hierarchy_graph.add_edge(node.parent, node.title)

            # Update parent's children list
            if node.parent:
                parent_data = self.hierarchy_graph.nodes[node.parent]
                if "children" not in parent_data:
                    parent_data["children"] = []
                parent_data["children"].append(node.title)

        except Exception as e:
            raise GraphError(f"Error adding node to hierarchy: {str(e)}")

    def get_node_hierarchy(self, node_title: str) -> Dict[str, any]:
        """Get the complete hierarchy for a node."""
        try:
            if node_title not in self.hierarchy_graph:
                raise GraphError(f"Node {node_title} does not exist")

            def build_hierarchy(node: str) -> Dict[str, any]:
                node_data = self.hierarchy_graph.nodes[node]
                hierarchy = {
                    "title": node,
                    "type": node_data["type"],
                    "metadata": node_data.get("metadata", {}),
                    "children": []
                }
                
                for child in node_data.get("children", []):
                    hierarchy["children"].append(build_hierarchy(child))
                
                return hierarchy

            return build_hierarchy(node_title)
        except Exception as e:
            raise GraphError(f"Error getting node hierarchy: {str(e)}")

    def find_orphaned_nodes(self) -> List[str]:
        """Find nodes that are not connected to any parent."""
        try:
            orphaned = []
            for node in self.hierarchy_graph.nodes():
                if not any(self.hierarchy_graph.has_edge(parent, node) 
                          for parent in self.hierarchy_graph.nodes()):
                    orphaned.append(node)
            return orphaned
        except Exception as e:
            raise GraphError(f"Error finding orphaned nodes: {str(e)}")

    def merge_semantic_and_hierarchy(self) -> nx.Graph:
        """Merge semantic and hierarchy relationships into a single graph."""
        try:
            merged_graph = nx.Graph()
            
            # Add all nodes from both graphs
            for node in self.hierarchy_graph.nodes():
                merged_graph.add_node(node, **self.hierarchy_graph.nodes[node])
            
            for node in self.semantic_graph.nodes():
                if node not in merged_graph:
                    merged_graph.add_node(node, **self.semantic_graph.nodes[node])
            
            # Add hierarchy edges
            for edge in self.hierarchy_graph.edges():
                merged_graph.add_edge(*edge, relationship="hierarchy")
            
            # Add semantic edges
            for edge in self.semantic_graph.edges():
                merged_graph.add_edge(*edge, relationship="semantic")
            
            return merged_graph
        except Exception as e:
            raise GraphError(f"Error merging graphs: {str(e)}")

    def analyze_node_relationships(self, node_title: str) -> Dict[str, List[str]]:
        """Analyze relationships between a node and other nodes in the graph."""
        try:
            if node_title not in self.hierarchy_graph:
                raise GraphError(f"Node {node_title} does not exist")

            relationships = {
                "parents": [],
                "children": [],
                "siblings": [],
                "semantic_related": []
            }

            # Get hierarchy relationships
            node_data = self.hierarchy_graph.nodes[node_title]
            if "parent" in node_data:
                relationships["parents"].append(node_data["parent"])
            
            relationships["children"] = node_data.get("children", [])

            # Get siblings (nodes with same parent)
            if relationships["parents"]:
                parent = relationships["parents"][0]
                parent_children = self.hierarchy_graph.nodes[parent].get("children", [])
                relationships["siblings"] = [child for child in parent_children 
                                          if child != node_title]

            # Get semantic relationships
            if node_title in self.semantic_graph:
                semantic_related = self.semantic_analyzer.find_related_notes(node_title)
                relationships["semantic_related"] = [rel["title"] for rel in semantic_related]

            return relationships
        except Exception as e:
            raise GraphError(f"Error analyzing node relationships: {str(e)}")

    def suggest_node_connections(self, node_title: str) -> List[Dict[str, any]]:
        """Suggest potential connections for a node based on semantic analysis."""
        try:
            if node_title not in self.hierarchy_graph:
                raise GraphError(f"Node {node_title} does not exist")

            suggestions = []
            node_data = self.hierarchy_graph.nodes[node_title]
            node_type = node_data["type"]

            # Get semantic relationships
            semantic_related = self.semantic_analyzer.find_related_notes(node_title)
            
            for related in semantic_related:
                related_title = related["title"]
                if related_title not in self.hierarchy_graph:
                    # Suggest adding to hierarchy
                    suggestions.append({
                        "type": "add_to_hierarchy",
                        "target": related_title,
                        "similarity": related["similarity"],
                        "shared_entities": related["shared_entities"]
                    })
                elif related_title not in node_data.get("children", []):
                    # Suggest connecting to existing node
                    suggestions.append({
                        "type": "connect_to_existing",
                        "target": related_title,
                        "similarity": related["similarity"],
                        "shared_entities": related["shared_entities"]
                    })

            return suggestions
        except Exception as e:
            raise GraphError(f"Error suggesting node connections: {str(e)}")

    def validate_hierarchy(self) -> List[Dict[str, any]]:
        """Validate the hierarchy structure and identify potential issues."""
        try:
            issues = []

            # Check for orphaned nodes
            orphaned = self.find_orphaned_nodes()
            if orphaned:
                issues.append({
                    "type": "orphaned_nodes",
                    "nodes": orphaned,
                    "severity": "high"
                })

            # Check for cycles
            try:
                nx.find_cycle(self.hierarchy_graph)
            except nx.NetworkXNoCycle:
                pass
            else:
                issues.append({
                    "type": "cycle_detected",
                    "severity": "high"
                })

            # Check for invalid node types
            for node in self.hierarchy_graph.nodes():
                node_type = self.hierarchy_graph.nodes[node]["type"]
                if node_type not in self.node_types:
                    issues.append({
                        "type": "invalid_node_type",
                        "node": node,
                        "invalid_type": node_type,
                        "severity": "medium"
                    })

            return issues
        except Exception as e:
            raise GraphError(f"Error validating hierarchy: {str(e)}") 
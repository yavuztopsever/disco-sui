from typing import Dict, Any, Optional, List
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

class AnalyzeRelationshipsTool(BaseTool):
    name = "analyze_relationships"
    description = "Analyze relationships between notes using semantic similarity and entity extraction"
    inputs = {
        "model_name": {
            "type": "string",
            "description": "The name of the sentence transformer model to use",
            "default": "all-MiniLM-L6-v2"
        },
        "similarity_threshold": {
            "type": "float",
            "description": "Minimum similarity score to consider a relationship",
            "default": 0.7
        }
    }
    output_type = "object"

    def forward(self, model_name: str = "all-MiniLM-L6-v2", 
                similarity_threshold: float = 0.7) -> Dict[str, Any]:
        try:
            # Get index directory
            index_dir = os.path.join(self.vault_path, ".obsidian", "index")
            if not os.path.exists(index_dir):
                return {
                    "success": False,
                    "message": "No indexed notes found"
                }

            # Initialize models
            transformer = SentenceTransformer(model_name)
            nlp = spacy.load("en_core_web_sm")

            # Collect all embeddings and metadata
            all_embeddings = []
            all_metadata = []
            all_texts = []

            for filename in os.listdir(index_dir):
                if not filename.endswith(".pkl"):
                    continue

                index_path = os.path.join(index_dir, filename)
                with open(index_path, "rb") as f:
                    index_data = pickle.load(f)

                all_embeddings.extend(index_data["embeddings"])
                all_metadata.extend([index_data["metadata"]] * len(index_data["embeddings"]))
                all_texts.extend(index_data["chunks"])

            if not all_embeddings:
                return {
                    "success": False,
                    "message": "No embeddings found"
                }

            # Convert to numpy array
            embeddings_array = np.array(all_embeddings)

            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings_array)

            # Create graph
            G = nx.Graph()

            # Add nodes
            unique_notes = {metadata["path"]: metadata for metadata in all_metadata}
            for path, metadata in unique_notes.items():
                G.add_node(path, **metadata)

            # Add edges based on similarity
            for i in range(len(similarity_matrix)):
                for j in range(i + 1, len(similarity_matrix)):
                    if similarity_matrix[i][j] >= similarity_threshold:
                        path1 = all_metadata[i]["path"]
                        path2 = all_metadata[j]["path"]
                        G.add_edge(path1, path2, 
                                 similarity=float(similarity_matrix[i][j]),
                                 shared_text=all_texts[i][:100] + "..." if all_texts[i] == all_texts[j] else None)

            # Extract entities and their relationships
            entity_relationships = defaultdict(list)
            for path, metadata in unique_notes.items():
                content = self._read_file(self._get_full_path(path))
                doc = nlp(content)
                
                for ent in doc.ents:
                    entity_relationships[ent.text].append({
                        "path": path,
                        "type": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })

            # Find communities
            communities = list(nx.community.louvain_communities(G))

            # Prepare results
            results = {
                "graph": {
                    "nodes": [{"path": path, **data} for path, data in G.nodes(data=True)],
                    "edges": [{"source": u, "target": v, **data} for u, v, data in G.edges(data=True)]
                },
                "communities": [
                    {
                        "id": i,
                        "notes": [{"path": path, **G.nodes[path]} for path in community]
                    }
                    for i, community in enumerate(communities)
                ],
                "entities": [
                    {
                        "text": entity,
                        "occurrences": occurrences
                    }
                    for entity, occurrences in entity_relationships.items()
                ]
            }

            # Save results
            results_path = os.path.join(self.vault_path, ".obsidian", "relationships.json")
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2)

            return {
                "success": True,
                "message": "Relationship analysis completed",
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to analyze relationships: {str(e)}",
                "error": str(e)
            }

class FindRelatedNotesTool(BaseTool):
    name = "find_related_notes"
    description = "Find notes related to a given note using semantic similarity and graph analysis"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note file, relative to the vault root"
        },
        "max_related": {
            "type": "integer",
            "description": "Maximum number of related notes to return",
            "default": 5
        }
    }
    output_type = "object"

    def forward(self, path: str, max_related: int = 5) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid note path: {path}")

            # Load relationships
            relationships_path = os.path.join(self.vault_path, ".obsidian", "relationships.json")
            if not os.path.exists(relationships_path):
                return {
                    "success": False,
                    "message": "No relationship data found. Run analyze_relationships first."
                }

            with open(relationships_path, "r") as f:
                relationships = json.load(f)

            # Create graph
            G = nx.Graph()
            for node in relationships["graph"]["nodes"]:
                G.add_node(node["path"], **{k: v for k, v in node.items() if k != "path"})
            for edge in relationships["graph"]["edges"]:
                G.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in ["source", "target"]})

            # Find related notes
            if path not in G:
                return {
                    "success": False,
                    "message": f"Note '{path}' not found in relationship graph"
                }

            # Get direct neighbors
            neighbors = list(G.neighbors(path))
            neighbor_data = [{"path": n, **G.nodes[n], "similarity": G[path][n]["similarity"]} for n in neighbors]
            neighbor_data.sort(key=lambda x: x["similarity"], reverse=True)

            # Get notes from same community
            community_notes = []
            for community in relationships["communities"]:
                if path in [note["path"] for note in community["notes"]]:
                    community_notes = [note for note in community["notes"] if note["path"] != path]
                    break

            # Get notes with shared entities
            shared_entities = []
            for entity in relationships["entities"]:
                occurrences = entity["occurrences"]
                if any(o["path"] == path for o in occurrences):
                    shared_entities.extend([
                        {"path": o["path"], "entity": entity["text"], "type": o["type"]}
                        for o in occurrences
                        if o["path"] != path
                    ])

            # Remove duplicates and sort by relevance
            shared_entities = list({(e["path"], e["entity"]): e for e in shared_entities}.values())
            shared_entities.sort(key=lambda x: len([e for e in shared_entities if e["path"] == x["path"]]), reverse=True)

            return {
                "success": True,
                "related_notes": {
                    "direct_connections": neighbor_data[:max_related],
                    "community_notes": community_notes[:max_related],
                    "shared_entities": shared_entities[:max_related]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to find related notes: {str(e)}",
                "error": str(e)
            }

class GenerateKnowledgeGraphTool(BaseTool):
    name = "generate_knowledge_graph"
    description = "Generate a knowledge graph from note relationships and entities"
    inputs = {
        "output_format": {
            "type": "string",
            "description": "The format to output the knowledge graph in",
            "enum": ["json", "dot", "gexf"],
            "default": "json"
        }
    }
    output_type = "object"

    def forward(self, output_format: str = "json") -> Dict[str, Any]:
        try:
            # Load relationships
            relationships_path = os.path.join(self.vault_path, ".obsidian", "relationships.json")
            if not os.path.exists(relationships_path):
                return {
                    "success": False,
                    "message": "No relationship data found. Run analyze_relationships first."
                }

            with open(relationships_path, "r") as f:
                relationships = json.load(f)

            # Create graph
            G = nx.Graph()
            for node in relationships["graph"]["nodes"]:
                G.add_node(node["path"], **{k: v for k, v in node.items() if k != "path"})
            for edge in relationships["graph"]["edges"]:
                G.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in ["source", "target"]})

            # Add entity nodes and edges
            for entity in relationships["entities"]:
                entity_id = f"entity_{entity['text']}"
                G.add_node(entity_id, type="entity", text=entity["text"])
                
                for occurrence in entity["occurrences"]:
                    G.add_edge(entity_id, occurrence["path"], 
                             type="mentions",
                             start=occurrence["start"],
                             end=occurrence["end"])

            # Export graph
            output_dir = os.path.join(self.vault_path, ".obsidian", "graphs")
            os.makedirs(output_dir, exist_ok=True)

            if output_format == "json":
                output_path = os.path.join(output_dir, "knowledge_graph.json")
                graph_data = nx.node_link_data(G)
                with open(output_path, "w") as f:
                    json.dump(graph_data, f, indent=2)
            elif output_format == "dot":
                output_path = os.path.join(output_dir, "knowledge_graph.dot")
                nx.drawing.nx_pydot.write_dot(G, output_path)
            elif output_format == "gexf":
                output_path = os.path.join(output_dir, "knowledge_graph.gexf")
                nx.write_gexf(G, output_path)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            return {
                "success": True,
                "message": f"Knowledge graph generated in {output_format} format",
                "output_path": output_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to generate knowledge graph: {str(e)}",
                "error": str(e)
            } 
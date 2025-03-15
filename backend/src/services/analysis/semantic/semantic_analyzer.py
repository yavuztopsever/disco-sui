from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel
from openai import OpenAI
from ...core.exceptions import LLMError
from ...core.config import settings
from ...features.note_management.note_manager import NoteManager
import networkx as nx
from collections import defaultdict

class SemanticNode(BaseModel):
    """Model for semantic nodes."""
    title: str
    content: str
    tags: List[str]
    related_nodes: List[str]
    parent_node: Optional[str]
    semantic_embedding: Optional[List[float]] = None
    entities: List[Dict[str, str]] = []
    topics: List[str] = []

class GraphEdge(BaseModel):
    """Model for a graph edge."""
    source: str
    target: str
    weight: float
    type: str
    metadata: Dict[str, Any]

class SemanticGraph(BaseModel):
    """Model for semantic graph."""
    nodes: Dict[str, SemanticNode]
    edges: List[Dict[str, Any]]
    clusters: Dict[str, List[str]]
    metadata: Dict[str, Any]

class SemanticAnalyzer:
    def __init__(self):
        self.note_manager = NoteManager()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.graph = nx.Graph()
        self.entity_index = defaultdict(list)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's API."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise LLMError(f"Error generating embedding: {str(e)}")

    def extract_entities_and_topics(self, content: str) -> tuple[List[Dict[str, str]], List[str]]:
        """Extract entities and topics from content using LLM."""
        try:
            prompt = f"""Analyze the following text and extract:
            1. Named entities (people, organizations, locations, etc.)
            2. Main topics or themes

            Text:
            {content}

            Format your response as JSON:
            {{
                "entities": [
                    {{"text": "entity name", "type": "entity type"}}
                ],
                "topics": ["topic1", "topic2"]
            }}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a text analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            result = response.choices[0].message.content
            # Parse the JSON response
            import json
            parsed = json.loads(result)
            return parsed["entities"], parsed["topics"]
        except Exception as e:
            print(f"Warning: Error extracting entities and topics: {str(e)}")
            return [], []

    def analyze_note(self, note_title: str) -> SemanticNode:
        """Analyze a note and create a semantic node."""
        try:
            # Get note content and metadata
            content = self.note_manager.get_note_content(note_title)
            metadata = self.note_manager.get_note_metadata(note_title)
            
            # Generate embedding
            embedding = self.generate_embedding(content)
            
            # Extract entities and topics
            entities, topics = self.extract_entities_and_topics(content)
            
            # Create semantic node
            node = SemanticNode(
                title=note_title,
                content=content,
                tags=metadata.tags,
                related_nodes=metadata.related_nodes,
                parent_node=metadata.parent_node,
                semantic_embedding=embedding,
                entities=entities,
                topics=topics
            )
            
            # Update graph
            self.graph.add_node(note_title, **node.dict())
            
            # Update entity index
            for entity in entities:
                self.entity_index[entity["text"]].append({
                    "note": note_title,
                    "type": entity["type"]
                })
            
            return node
        except Exception as e:
            raise LLMError(f"Error analyzing note {note_title}: {str(e)}")

    def build_semantic_graph(self, note_titles: List[str]) -> SemanticGraph:
        """Build a semantic graph from a list of notes."""
        try:
            nodes = {}
            edges = []
            clusters = {}
            
            # Create nodes
            for title in note_titles:
                nodes[title] = self.analyze_note(title)
            
            # Create edges based on semantic similarity and shared entities
            for i, title1 in enumerate(note_titles):
                for title2 in note_titles[i+1:]:
                    # Calculate semantic similarity
                    similarity = self.calculate_similarity(
                        nodes[title1].semantic_embedding,
                        nodes[title2].semantic_embedding
                    )
                    
                    # Find shared entities
                    shared_entities = self._find_shared_entities(title1, title2)
                    
                    # Create edge if similarity is high or there are shared entities
                    if similarity > 0.7 or shared_entities:
                        edge_data = {
                            "source": title1,
                            "target": title2,
                            "weight": similarity,
                            "shared_entities": shared_entities
                        }
                        edges.append(edge_data)
                        self.graph.add_edge(title1, title2, **edge_data)
            
            # Create clusters using community detection
            clusters = self.detect_communities(nodes, edges)
            
            return SemanticGraph(
                nodes=nodes,
                edges=edges,
                clusters=clusters
            )
        except Exception as e:
            raise LLMError(f"Error building semantic graph: {str(e)}")

    def _find_shared_entities(self, note1: str, note2: str) -> List[Dict[str, str]]:
        """Find entities shared between two notes."""
        try:
            shared = []
            for entity, occurrences in self.entity_index.items():
                notes = [o["note"] for o in occurrences]
                if note1 in notes and note2 in notes:
                    shared.append({
                        "text": entity,
                        "type": occurrences[0]["type"]
                    })
            return shared
        except Exception as e:
            print(f"Warning: Error finding shared entities: {str(e)}")
            return []

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            import numpy as np
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        except Exception as e:
            raise LLMError(f"Error calculating similarity: {str(e)}")

    def detect_communities(self, nodes: Dict[str, SemanticNode], edges: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Detect communities in the semantic graph."""
        try:
            # Use Louvain algorithm for community detection
            communities = nx.community.louvain_communities(self.graph)
            
            # Organize communities by their main topics
            community_dict = {}
            for i, community in enumerate(communities):
                # Get main topics for the community
                community_topics = set()
                for node in community:
                    community_topics.update(nodes[node].topics)
                
                # Create a descriptive name for the community
                community_name = f"Community_{i}_{'_'.join(sorted(list(community_topics))[:3])}"
                community_dict[community_name] = list(community)
            
            return community_dict
        except Exception as e:
            raise LLMError(f"Error detecting communities: {str(e)}")

    def find_related_notes(self, note_title: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find semantically related notes."""
        try:
            if note_title not in self.graph:
                # If note is not in graph, analyze it first
                self.analyze_note(note_title)
            
            # Get direct neighbors
            neighbors = list(self.graph.neighbors(note_title))
            neighbor_data = []
            
            for neighbor in neighbors:
                edge_data = self.graph[note_title][neighbor]
                neighbor_data.append({
                    "title": neighbor,
                    "similarity": edge_data["weight"],
                    "shared_entities": edge_data.get("shared_entities", [])
                })
            
            # Sort by similarity and return top results
            neighbor_data.sort(key=lambda x: x["similarity"], reverse=True)
            return neighbor_data[:n_results]
        except Exception as e:
            raise LLMError(f"Error finding related notes: {str(e)}")

    def remove_note(self, note_title: str) -> None:
        """Remove a note from the semantic graph and entity index."""
        try:
            # Remove from graph
            if note_title in self.graph:
                self.graph.remove_node(note_title)
            
            # Remove from entity index
            for entity in list(self.entity_index.keys()):
                self.entity_index[entity] = [
                    o for o in self.entity_index[entity]
                    if o["note"] != note_title
                ]
                if not self.entity_index[entity]:
                    del self.entity_index[entity]
        except Exception as e:
            print(f"Warning: Error removing note from semantic analysis: {str(e)}")

    def suggest_tags(self, note_title: str) -> List[str]:
        """Suggest tags for a note based on semantic analysis."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for tag suggestion
            prompt = f"""Based on the following content, suggest relevant tags.
            Tags should be simple entities (concepts, places, brands, companies, services).
            Do not include too many details in tags.
            Return only the tags, one per line.

            Content:
            {content}

            Suggested tags:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests relevant tags for content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )

            # Process response
            tags = response.choices[0].message.content.strip().split('\n')
            return [tag.strip() for tag in tags if tag.strip()]
        except Exception as e:
            raise LLMError(f"Error suggesting tags: {str(e)}")

    def analyze_note_relationships(self, note_title: str) -> Dict[str, List[str]]:
        """Analyze relationships between notes."""
        try:
            # Get related notes
            related_notes = self.find_related_notes(note_title)
            
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            
            # Create prompt for relationship analysis
            prompt = f"""Based on the following content and related notes, analyze the relationships.
            Identify parent-child relationships, references, and other connections.
            Return the analysis in a structured format.

            Content:
            {content}

            Related notes:
            {chr(10).join(f"- {note['title']} (similarity: {note['similarity']:.2f})" for note in related_notes)}

            Analysis:"""

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes relationships between notes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Process response
            analysis = response.choices[0].message.content.strip()
            
            return {
                "analysis": analysis,
                "related_notes": [note["title"] for note in related_notes]
            }
        except Exception as e:
            raise LLMError(f"Error analyzing note relationships: {str(e)}") 
from typing import Dict, Any, Optional, List
from .base_tools import BaseTool
import os
import json
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import faiss
import pickle
from pathlib import Path

from ..core.tool_interfaces import AnalysisTool

class MetadataExtractionTool(AnalysisTool):
    """Tool for extracting metadata from content."""
    
    async def forward(
        self,
        content: str,
        metadata_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Extract metadata from content.
        
        Args:
            content: Content to analyze
            metadata_types: Types of metadata to extract
            **kwargs: Additional extraction parameters
            
        Returns:
            Extracted metadata
        """
        return await self.extract_metadata(content, metadata_types, **kwargs)

class IndexAnalysisTool(AnalysisTool):
    """Tool for analyzing content structure and organization."""
    
    async def forward(
        self,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content structure.
        
        Args:
            content: Content to analyze
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        return await self.analyze_content(content, analysis_type="structure", **kwargs)

class LinkAnalysisTool(AnalysisTool):
    """Tool for analyzing links between content."""
    
    async def forward(
        self,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content links.
        
        Args:
            content: Content to analyze
            **kwargs: Additional analysis parameters
            
        Returns:
            Analysis results
        """
        return await self.analyze_content(content, analysis_type="links", **kwargs)

class IndexNoteTool(BaseTool):
    name = "index_note"
    description = "Index a note for semantic search"
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the note file, relative to the vault root"
        },
        "model_name": {
            "type": "string",
            "description": "The name of the sentence transformer model to use",
            "default": "all-MiniLM-L6-v2"
        },
        "chunk_size": {
            "type": "integer",
            "description": "The size of text chunks to index",
            "default": 512
        },
        "chunk_overlap": {
            "type": "integer",
            "description": "The overlap between chunks",
            "default": 50
        }
    }
    output_type = "object"

    def forward(self, path: str, model_name: str = "all-MiniLM-L6-v2", 
                chunk_size: int = 512, chunk_overlap: int = 50) -> Dict[str, Any]:
        try:
            # Validate path
            if not self._validate_path(path):
                raise ValueError(f"Invalid note path: {path}")

            # Get full path
            note_path = self._get_full_path(path)

            # Check if note exists
            if not os.path.exists(note_path):
                raise FileNotFoundError(f"Note not found: {path}")

            # Read note content
            content = self._read_file(note_path)
            frontmatter = self._get_frontmatter(content)

            # Remove frontmatter from content
            content = content.replace("---", "", 2).strip()

            # Initialize model
            model = SentenceTransformer(model_name)

            # Split content into chunks
            chunks = self._split_into_chunks(content, chunk_size, chunk_overlap)

            # Generate embeddings
            embeddings = model.encode(chunks)

            # Create index directory if it doesn't exist
            index_dir = os.path.join(self.vault_path, ".obsidian", "index")
            os.makedirs(index_dir, exist_ok=True)

            # Save embeddings and metadata
            note_id = os.path.splitext(os.path.basename(path))[0]
            index_path = os.path.join(index_dir, f"{note_id}.pkl")
            
            index_data = {
                "embeddings": embeddings,
                "chunks": chunks,
                "metadata": {
                    "path": path,
                    "title": frontmatter.get("title", ""),
                    "type": frontmatter.get("type", "note"),
                    "tags": frontmatter.get("tags", []),
                    "last_modified": datetime.now().isoformat()
                }
            }

            with open(index_path, "wb") as f:
                pickle.dump(index_data, f)

            return {
                "success": True,
                "message": f"Note '{path}' indexed successfully",
                "chunks": len(chunks)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to index note: {str(e)}",
                "error": str(e)
            }

    def _split_into_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            if end > text_length:
                end = text_length

            chunk = text[start:end]
            chunks.append(chunk)
            start = end - chunk_overlap

        return chunks

class SearchNotesTool(BaseTool):
    name = "search_notes"
    description = "Search notes using semantic similarity"
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "model_name": {
            "type": "string",
            "description": "The name of the sentence transformer model to use",
            "default": "all-MiniLM-L6-v2"
        },
        "top_k": {
            "type": "integer",
            "description": "Number of results to return",
            "default": 5
        }
    }
    output_type = "object"

    def forward(self, query: str, model_name: str = "all-MiniLM-L6-v2", 
                top_k: int = 5) -> Dict[str, Any]:
        try:
            # Initialize model
            model = SentenceTransformer(model_name)

            # Generate query embedding
            query_embedding = model.encode([query])[0]

            # Get index directory
            index_dir = os.path.join(self.vault_path, ".obsidian", "index")
            if not os.path.exists(index_dir):
                return {
                    "success": False,
                    "message": "No indexed notes found"
                }

            # Search through all indices
            results = []
            for filename in os.listdir(index_dir):
                if not filename.endswith(".pkl"):
                    continue

                index_path = os.path.join(index_dir, filename)
                with open(index_path, "rb") as f:
                    index_data = pickle.load(f)

                # Calculate similarities
                similarities = np.dot(index_data["embeddings"], query_embedding)
                top_indices = np.argsort(similarities)[-top_k:][::-1]

                # Add results
                for idx in top_indices:
                    results.append({
                        "path": index_data["metadata"]["path"],
                        "title": index_data["metadata"]["title"],
                        "chunk": index_data["chunks"][idx],
                        "similarity": float(similarities[idx])
                    })

            # Sort all results by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = results[:top_k]

            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to search notes: {str(e)}",
                "error": str(e)
            }

class ClusterNotesTool(BaseTool):
    name = "cluster_notes"
    description = "Cluster notes based on semantic similarity"
    inputs = {
        "model_name": {
            "type": "string",
            "description": "The name of the sentence transformer model to use",
            "default": "all-MiniLM-L6-v2"
        },
        "n_clusters": {
            "type": "integer",
            "description": "Number of clusters to create",
            "default": 5
        }
    }
    output_type = "object"

    def forward(self, model_name: str = "all-MiniLM-L6-v2", 
                n_clusters: int = 5) -> Dict[str, Any]:
        try:
            # Get index directory
            index_dir = os.path.join(self.vault_path, ".obsidian", "index")
            if not os.path.exists(index_dir):
                return {
                    "success": False,
                    "message": "No indexed notes found"
                }

            # Collect all embeddings and metadata
            all_embeddings = []
            all_metadata = []

            for filename in os.listdir(index_dir):
                if not filename.endswith(".pkl"):
                    continue

                index_path = os.path.join(index_dir, filename)
                with open(index_path, "rb") as f:
                    index_data = pickle.load(f)

                all_embeddings.extend(index_data["embeddings"])
                all_metadata.extend([index_data["metadata"]] * len(index_data["embeddings"]))

            if not all_embeddings:
                return {
                    "success": False,
                    "message": "No embeddings found"
                }

            # Convert to numpy array
            embeddings_array = np.array(all_embeddings)

            # Perform clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(all_embeddings)))
            clusters = kmeans.fit_predict(embeddings_array)

            # Organize results
            results = []
            for i in range(n_clusters):
                cluster_indices = np.where(clusters == i)[0]
                cluster_notes = []
                
                for idx in cluster_indices:
                    metadata = all_metadata[idx]
                    if metadata not in cluster_notes:  # Avoid duplicates
                        cluster_notes.append(metadata)

                if cluster_notes:
                    results.append({
                        "cluster_id": i,
                        "notes": cluster_notes,
                        "size": len(cluster_notes)
                    })

            return {
                "success": True,
                "clusters": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to cluster notes: {str(e)}",
                "error": str(e)
            } 
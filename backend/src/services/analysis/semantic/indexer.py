import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from ...core.exceptions import RAGError
from ...core.config import settings
from ...features.note_management.note_manager import NoteManager

class Indexer:
    def __init__(self):
        self.note_manager = NoteManager()
        self.client = chromadb.Client(Settings(
            persist_directory=settings.RAG_VECTOR_DB_PATH,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection("notes")

    def chunk_content(self, content: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, str]]:
        """Split content into chunks for indexing."""
        try:
            chunks = []
            words = content.split()
            current_chunk = []
            current_size = 0
            
            for word in words:
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space
                
                if current_size >= chunk_size:
                    chunks.append(" ".join(current_chunk))
                    # Keep overlap words for next chunk
                    overlap_words = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_words
                    current_size = sum(len(word) + 1 for word in overlap_words)
            
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            return [{"text": chunk, "metadata": {}} for chunk in chunks]
        except Exception as e:
            raise RAGError(f"Error chunking content: {str(e)}")

    def index_note(self, note_title: str) -> None:
        """Index a note in the vector database."""
        try:
            # Get note content
            content = self.note_manager.get_note_content(note_title)
            metadata = self.note_manager.get_note_metadata(note_title)
            
            # Chunk content
            chunks = self.chunk_content(content)
            
            # Prepare documents for indexing
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{note_title}_{i}"
                documents.append(chunk["text"])
                metadatas.append({
                    "title": note_title,
                    "tags": metadata.tags,
                    "type": metadata.type,
                    "parent_node": metadata.parent_node,
                    "related_nodes": metadata.related_nodes,
                    "created_at": metadata.created_at,
                    "updated_at": metadata.updated_at,
                    "chunk_index": i
                })
                ids.append(chunk_id)
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            raise RAGError(f"Error indexing note {note_title}: {str(e)}")

    def index_directory(self, directory_path: str) -> Dict[str, str]:
        """Index all notes in a directory."""
        try:
            results = {}
            note_dir = Path(directory_path)
            
            for note_file in note_dir.glob("**/*.md"):
                try:
                    note_title = note_file.stem
                    self.index_note(note_title)
                    results[str(note_file)] = "Successfully indexed"
                except Exception as e:
                    results[str(note_file)] = f"Error: {str(e)}"
            
            return results
        except Exception as e:
            raise RAGError(f"Error indexing directory {directory_path}: {str(e)}")

    def search_notes(self, query: str, n_results: int = 5) -> List[Dict[str, any]]:
        """Search for relevant notes using the vector database."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Process results
            processed_results = []
            for i in range(len(results['documents'][0])):
                processed_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            
            return processed_results
        except Exception as e:
            raise RAGError(f"Error searching notes: {str(e)}")

    def update_index(self, note_title: str) -> None:
        """Update the index for a note."""
        try:
            # Delete existing chunks
            self.collection.delete(
                where={"title": note_title}
            )
            
            # Re-index the note
            self.index_note(note_title)
        except Exception as e:
            raise RAGError(f"Error updating index for note {note_title}: {str(e)}")

    def delete_from_index(self, note_title: str) -> None:
        """Delete a note from the index."""
        try:
            self.collection.delete(
                where={"title": note_title}
            )
        except Exception as e:
            raise RAGError(f"Error deleting note {note_title} from index: {str(e)}")

    def get_note_chunks(self, note_title: str) -> List[Dict[str, any]]:
        """Get all chunks for a note."""
        try:
            results = self.collection.get(
                where={"title": note_title}
            )
            
            chunks = []
            for i in range(len(results['documents'])):
                chunks.append({
                    "text": results['documents'][i],
                    "metadata": results['metadatas'][i],
                    "id": results['ids'][i]
                })
            
            return chunks
        except Exception as e:
            raise RAGError(f"Error getting chunks for note {note_title}: {str(e)}") 
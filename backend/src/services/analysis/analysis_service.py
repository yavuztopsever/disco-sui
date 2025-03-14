from typing import Dict, List, Optional, Union
from pathlib import Path
import asyncio
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings
import tiktoken

from ..base_service import BaseService
from ...core.exceptions import AnalysisError

class AnalysisConfig(BaseModel):
    """Configuration for analysis service."""
    vault_path: Path
    db_path: Path
    collection_name: str = "obsidian_notes"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 500
    chunk_overlap: int = 50
    batch_size: int = 32
    reindex_interval: int = 3600  # 1 hour
    max_tokens_per_chunk: int = 1000

class SearchResult(BaseModel):
    """Model for search results."""
    content: str
    metadata: Dict[str, any]
    score: float
    source_path: Path
    chunk_index: int

class AnalysisService(BaseService):
    """Service for semantic analysis and indexing of notes."""

    def _initialize(self) -> None:
        """Initialize analysis service configuration and resources."""
        self.config_model = AnalysisConfig(**self.config)
        self._client = chromadb.PersistentClient(path=str(self.config_model.db_path))
        self._collection = self._client.get_or_create_collection(
            name=self.config_model.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._tokenizer = tiktoken.encoding_for_model(self.config_model.embedding_model)
        self._background_task = None
        self._running = False
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.config_model.db_path.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the analysis service."""
        if self._running:
            return

        self._running = True
        self._background_task = asyncio.create_task(self._reindex_periodically())

    async def stop(self) -> None:
        """Stop the analysis service."""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def health_check(self) -> bool:
        """Check if the analysis service is healthy."""
        try:
            self._collection.count()
            return True
        except Exception:
            return False

    async def _reindex_periodically(self) -> None:
        """Periodically reindex the vault."""
        while self._running:
            try:
                await self._reindex_vault()
            except Exception as e:
                raise AnalysisError(f"Error reindexing vault: {str(e)}")
            finally:
                await asyncio.sleep(self.config_model.reindex_interval)

    async def _reindex_vault(self) -> None:
        """Reindex all notes in the vault."""
        try:
            # Get all markdown files
            markdown_files = list(self.config_model.vault_path.rglob("*.md"))
            
            # Process files in batches
            batch_size = self.config_model.batch_size
            for i in range(0, len(markdown_files), batch_size):
                batch = markdown_files[i:i + batch_size]
                await self._process_files_batch(batch)

        except Exception as e:
            raise AnalysisError(f"Failed to reindex vault: {str(e)}")

    async def _process_files_batch(self, files: List[Path]) -> None:
        """Process a batch of files for indexing."""
        documents = []
        metadatas = []
        ids = []

        for file in files:
            try:
                content = file.read_text()
                chunks = self._chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    doc_id = f"{file.stem}_{i}"
                    documents.append(chunk)
                    metadatas.append({
                        "source": str(file.relative_to(self.config_model.vault_path)),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "indexed_at": datetime.now().isoformat()
                    })
                    ids.append(doc_id)

            except Exception as e:
                raise AnalysisError(f"Failed to process file {file}: {str(e)}")

        if documents:
            self._collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks based on token count and overlap."""
        tokens = self._tokenizer.encode(text)
        chunks = []
        
        i = 0
        while i < len(tokens):
            # Get chunk of tokens
            chunk_end = min(i + self.config_model.max_tokens_per_chunk, len(tokens))
            chunk_tokens = tokens[i:chunk_end]
            
            # Decode chunk back to text
            chunk_text = self._tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move to next chunk with overlap
            i += self.config_model.max_tokens_per_chunk - self.config_model.chunk_overlap

        return chunks

    async def semantic_search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """Perform semantic search over the indexed notes."""
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )

            search_results = []
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Convert distance to similarity score (0-1)
                score = 1 - (distance / 2)  # Cosine distance to similarity
                
                if score < threshold:
                    continue

                search_results.append(SearchResult(
                    content=doc,
                    metadata=metadata,
                    score=score,
                    source_path=self.config_model.vault_path / metadata["source"],
                    chunk_index=metadata["chunk_index"]
                ))

            return sorted(search_results, key=lambda x: x.score, reverse=True)

        except Exception as e:
            raise AnalysisError(f"Failed to perform semantic search: {str(e)}")

    async def get_similar_notes(
        self,
        note_path: Union[str, Path],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """Find semantically similar notes to a given note."""
        try:
            note_path = Path(note_path)
            if not note_path.exists():
                raise AnalysisError(f"Note not found: {note_path}")

            content = note_path.read_text()
            return await self.semantic_search(content, limit, threshold)

        except Exception as e:
            raise AnalysisError(f"Failed to find similar notes: {str(e)}")

    async def analyze_note_content(self, content: str) -> Dict[str, any]:
        """Analyze note content for semantic information."""
        # Implementation for content analysis
        pass 
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import logging
from pathlib import Path
import asyncio
import json

logger = logging.getLogger(__name__)

class Memory(BaseModel):
    """Model for storing interaction memories."""
    id: str
    timestamp: datetime
    user_input: str
    result: Dict[str, Any]
    context: Dict[str, Any]
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

class MemoryConfig(BaseModel):
    """Configuration for memory management."""
    max_short_term_memories: int = 100
    max_long_term_memories: int = 1000
    relevance_threshold: float = 0.5
    cleanup_interval: int = 3600  # 1 hour
    storage_path: Path = Path(".memories")

class MemoryManager:
    """Enhanced memory manager for agent interactions."""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.short_term_memory: List[Memory] = []
        self.long_term_memory: List[Memory] = []
        self._setup_storage()
        
    def _setup_storage(self):
        """Setup memory storage."""
        self.config.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def store_interaction(
        self,
        user_input: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Store an interaction in memory."""
        memory = Memory(
            id=f"mem_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            user_input=user_input,
            result=result,
            context=context
        )
        
        # Add to short-term memory
        self.short_term_memory.append(memory)
        
        # Manage memory size
        if len(self.short_term_memory) > self.config.max_short_term_memories:
            await self._consolidate_memories()
            
        # Save to storage
        await self._save_memory(memory)
        
    async def get_relevant_context(
        self,
        query: str,
        min_relevance: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get relevant context from memories."""
        min_relevance = min_relevance or self.config.relevance_threshold
        
        # Search both memory stores
        relevant_memories = []
        
        # Check short-term memory
        for memory in self.short_term_memory:
            relevance = await self._calculate_relevance(query, memory)
            if relevance >= min_relevance:
                memory.relevance_score = relevance
                relevant_memories.append(memory)
                
        # Check long-term memory
        for memory in self.long_term_memory:
            relevance = await self._calculate_relevance(query, memory)
            if relevance >= min_relevance:
                memory.relevance_score = relevance
                relevant_memories.append(memory)
                
        # Sort by relevance
        relevant_memories.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update access metrics
        for memory in relevant_memories:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            
        # Merge contexts from relevant memories
        merged_context = {}
        for memory in relevant_memories:
            merged_context.update(memory.context)
            
        return merged_context
        
    async def optimize_retrieval(
        self,
        user_input: str,
        result: Dict[str, Any]
    ):
        """Optimize memory retrieval based on interaction results."""
        try:
            # Update relevance scores based on result
            success = result.get("success", False)
            
            if success:
                # Increase relevance of similar memories
                for memory in self.short_term_memory + self.long_term_memory:
                    similarity = await self._calculate_similarity(
                        user_input,
                        memory.user_input
                    )
                    if similarity > self.config.relevance_threshold:
                        memory.relevance_score *= 1.1  # Increase score by 10%
                        
            # Cleanup if needed
            await self._cleanup_old_memories()
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            
    async def optimize_storage(self):
        """Optimize memory storage."""
        try:
            # Consolidate memories if needed
            if len(self.short_term_memory) > self.config.max_short_term_memories * 0.9:
                await self._consolidate_memories()
                
            # Remove low-relevance memories
            await self._cleanup_low_relevance_memories()
            
            # Compact storage
            await self._compact_storage()
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
            
    async def cleanup(self):
        """Clean up memory resources."""
        try:
            # Save all memories
            for memory in self.short_term_memory + self.long_term_memory:
                await self._save_memory(memory)
                
            # Clear short-term memory
            self.short_term_memory.clear()
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            
    async def _consolidate_memories(self):
        """Consolidate short-term memories into long-term storage."""
        # Sort by relevance and access patterns
        self.short_term_memory.sort(
            key=lambda x: (x.relevance_score, x.access_count),
            reverse=True
        )
        
        # Move most relevant memories to long-term storage
        memories_to_move = self.short_term_memory[
            :self.config.max_short_term_memories // 2
        ]
        
        # Update long-term memory
        self.long_term_memory.extend(memories_to_move)
        
        # Remove moved memories from short-term
        self.short_term_memory = self.short_term_memory[
            self.config.max_short_term_memories // 2:
        ]
        
        # Ensure long-term memory size
        if len(self.long_term_memory) > self.config.max_long_term_memories:
            # Remove least relevant memories
            self.long_term_memory.sort(
                key=lambda x: (x.relevance_score, x.access_count)
            )
            self.long_term_memory = self.long_term_memory[
                :self.config.max_long_term_memories
            ]
            
    async def _calculate_relevance(
        self,
        query: str,
        memory: Memory
    ) -> float:
        """Calculate relevance score between query and memory."""
        try:
            # Calculate base similarity
            input_similarity = await self._calculate_similarity(
                query,
                memory.user_input
            )
            
            # Apply decay based on time
            time_decay = self._calculate_time_decay(memory.timestamp)
            
            # Apply boost based on access patterns
            access_boost = min(memory.access_count / 10, 1.0)
            
            # Combine factors
            relevance = (
                input_similarity * 0.6 +  # Base similarity
                time_decay * 0.2 +        # Time decay
                access_boost * 0.2        # Access patterns
            )
            
            return min(max(relevance, 0.0), 1.0)  # Ensure range [0, 1]
            
        except Exception as e:
            logger.error(f"Relevance calculation failed: {e}")
            return 0.0
            
    async def _calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate similarity between two texts."""
        # TODO: Implement more sophisticated similarity calculation
        # For now, use simple word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
        
    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """Calculate time-based decay factor."""
        age = (datetime.now() - timestamp).total_seconds()
        # Exponential decay with half-life of 24 hours
        half_life = 24 * 3600  # 24 hours in seconds
        decay = 2 ** (-age / half_life)
        return decay
        
    async def _cleanup_old_memories(self):
        """Clean up old memories based on relevance and age."""
        current_time = datetime.now()
        
        # Remove old memories with low relevance
        self.long_term_memory = [
            mem for mem in self.long_term_memory
            if (
                mem.relevance_score > self.config.relevance_threshold or
                (current_time - mem.timestamp).days < 7  # Keep recent memories
            )
        ]
        
    async def _cleanup_low_relevance_memories(self):
        """Remove memories with consistently low relevance."""
        threshold = self.config.relevance_threshold / 2
        
        self.long_term_memory = [
            mem for mem in self.long_term_memory
            if mem.relevance_score > threshold
        ]
        
    async def _save_memory(self, memory: Memory):
        """Save memory to persistent storage."""
        try:
            file_path = self.config.storage_path / f"{memory.id}.json"
            with open(file_path, 'w') as f:
                json.dump(memory.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save memory {memory.id}: {e}")
            
    async def _compact_storage(self):
        """Compact memory storage."""
        try:
            # Remove files for deleted memories
            existing_ids = {mem.id for mem in self.short_term_memory + self.long_term_memory}
            
            for file_path in self.config.storage_path.glob("*.json"):
                memory_id = file_path.stem
                if memory_id not in existing_ids:
                    file_path.unlink()
                    
        except Exception as e:
            logger.error(f"Storage compaction failed: {e}") 
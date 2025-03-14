from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import logging
from pathlib import Path
import asyncio
import json
from collections import OrderedDict
import pickle
import aiofiles
import aiosqlite
import zlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Statistics for cache operations."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    compression_ratio: float = 0.0

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
    compressed: bool = False
    size_bytes: int = 0

class MemoryConfig(BaseModel):
    """Configuration for memory management."""
    cache_size: int = 10000  # Combined cache size
    compression_threshold: int = 1024  # Bytes
    compression_level: int = 6
    batch_size: int = 100
    cleanup_interval: int = 3600  # 1 hour
    storage_path: Path = Path(".memories")
    db_path: Path = Path(".memory.db")
    max_memory_size: int = 1000000000  # 1GB
    enable_compression: bool = True
    vacuum_threshold: float = 0.7

class UnifiedCache:
    """Unified LRU cache with tiered eviction."""
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.cache: OrderedDict[str, Memory] = OrderedDict()
        self.stats = CacheStats()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._compression_queue: List[str] = []
        
    async def get(self, key: str) -> Optional[Memory]:
        """Get item from cache with automatic decompression."""
        if key not in self.cache:
            self.stats.misses += 1
            return None
            
        memory = self.cache.pop(key)
        self.cache[key] = memory  # Move to end (most recently used)
        self.stats.hits += 1
        
        if memory.compressed:
            memory = await self._decompress_memory(memory)
            
        return memory
        
    async def put(self, key: str, memory: Memory) -> List[Memory]:
        """Put item in cache with automatic compression."""
        evicted = []
        
        # Compress if needed
        if (
            self.config.enable_compression and
            not memory.compressed and
            memory.size_bytes > self.config.compression_threshold
        ):
            self._compression_queue.append(key)
            asyncio.create_task(self._process_compression_queue())
            
        # Evict items if needed
        while self.stats.total_size + memory.size_bytes > self.config.max_memory_size:
            if not self.cache:
                break
            evicted_key, evicted_memory = self.cache.popitem(last=False)
            self.stats.total_size -= evicted_memory.size_bytes
            self.stats.evictions += 1
            evicted.append(evicted_memory)
            
        # Add new item
        self.cache[key] = memory
        self.stats.total_size += memory.size_bytes
        
        return evicted
        
    async def _process_compression_queue(self):
        """Process queued items for compression."""
        while self._compression_queue:
            key = self._compression_queue.pop(0)
            if key in self.cache:
                memory = self.cache[key]
                compressed_memory = await self._compress_memory(memory)
                self.cache[key] = compressed_memory
                
    async def _compress_memory(self, memory: Memory) -> Memory:
        """Compress memory data."""
        if memory.compressed:
            return memory
            
        try:
            data = pickle.dumps(memory.dict())
            compressed = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: zlib.compress(data, self.config.compression_level)
            )
            
            memory.size_bytes = len(compressed)
            memory.compressed = True
            self.stats.compression_ratio = len(compressed) / len(data)
            
            return memory
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return memory
            
    async def _decompress_memory(self, memory: Memory) -> Memory:
        """Decompress memory data."""
        if not memory.compressed:
            return memory
            
        try:
            decompressed = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: zlib.decompress(pickle.dumps(memory.dict()))
            )
            
            memory_dict = pickle.loads(decompressed)
            memory = Memory(**memory_dict)
            memory.compressed = False
            
            return memory
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return memory

class MemoryManager:
    """Manages memory system with unified caching."""
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.cache = UnifiedCache(self.config)
        self._setup_storage()
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
    def _setup_storage(self):
        """Setup memory storage."""
        self.config.storage_path.mkdir(parents=True, exist_ok=True)
        asyncio.create_task(self._initialize_db())
        
    async def _initialize_db(self):
        """Initialize SQLite database."""
        async with aiosqlite.connect(self.config.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    data BLOB,
                    timestamp DATETIME,
                    relevance_score REAL,
                    access_count INTEGER,
                    size_bytes INTEGER,
                    compressed BOOLEAN
                )
            """)
            await db.commit()
            
    async def store_interaction(
        self,
        user_input: str,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Store an interaction in memory system."""
        memory = Memory(
            id=f"mem_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            user_input=user_input,
            result=result,
            context=context,
            size_bytes=len(pickle.dumps(result)) + len(pickle.dumps(context))
        )
        
        # Store in cache
        evicted = await self.cache.put(memory.id, memory)
        
        # Store evicted items in database
        if evicted:
            await self._batch_store_memories(evicted)
            
        # Store new memory in database
        await self._store_memory(memory)
        
        return memory.id
        
    async def get_relevant_context(
        self,
        query: str,
        min_relevance: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get relevant context from memories."""
        min_relevance = min_relevance or self.config.relevance_threshold
        relevant_memories = []
        
        # Search cache
        cache_memories = await self._search_cache(query, min_relevance)
        relevant_memories.extend(cache_memories)
        
        # Search database if needed
        if len(relevant_memories) < self.config.batch_size:
            db_memories = await self._search_database(query, min_relevance)
            relevant_memories.extend(db_memories)
            
        # Update access metrics
        for memory in relevant_memories:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            await self.cache.put(memory.id, memory)
            
        # Merge contexts
        return self._merge_contexts(relevant_memories)
        
    async def _search_cache(
        self,
        query: str,
        min_relevance: float
    ) -> List[Memory]:
        """Search cache for relevant memories."""
        relevant = []
        
        for memory in self.cache.cache.values():
            relevance = await self._calculate_relevance(query, memory)
            if relevance >= min_relevance:
                memory.relevance_score = relevance
                relevant.append(memory)
                
        return sorted(relevant, key=lambda x: x.relevance_score, reverse=True)
        
    async def _search_database(
        self,
        query: str,
        min_relevance: float
    ) -> List[Memory]:
        """Search database for relevant memories."""
        relevant = []
        
        async with aiosqlite.connect(self.config.db_path) as db:
            cursor = await db.execute("SELECT * FROM memories")
            async for row in cursor:
                memory = Memory(**pickle.loads(row[1]))
                relevance = await self._calculate_relevance(query, memory)
                if relevance >= min_relevance:
                    memory.relevance_score = relevance
                    relevant.append(memory)
                    
        return sorted(relevant, key=lambda x: x.relevance_score, reverse=True)
        
    def _merge_contexts(self, memories: List[Memory]) -> Dict[str, Any]:
        """Merge contexts from memories."""
        merged = {}
        for memory in memories:
            for key, value in memory.context.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, dict):
                    merged[key].update(value)
                elif isinstance(value, list):
                    merged[key].extend(value)
                    
        return merged
        
    async def _batch_store_memories(self, memories: List[Memory]):
        """Store multiple memories in database."""
        async with aiosqlite.connect(self.config.db_path) as db:
            await db.executemany(
                """
                INSERT OR REPLACE INTO memories
                (id, data, timestamp, relevance_score, access_count, size_bytes, compressed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        memory.id,
                        pickle.dumps(memory.dict()),
                        memory.timestamp,
                        memory.relevance_score,
                        memory.access_count,
                        memory.size_bytes,
                        memory.compressed
                    )
                    for memory in memories
                ]
            )
            await db.commit()
            
    async def _periodic_cleanup(self):
        """Periodically clean up old memories."""
        while True:
            await asyncio.sleep(self.config.cleanup_interval)
            await self._cleanup_old_memories()
            await self._optimize_storage()
            
    async def cleanup(self):
        """Clean up memory resources."""
        try:
            # Cancel cleanup task
            self._cleanup_task.cancel()
            
            # Store all cache items
            memories = list(self.cache.cache.values())
            await self._batch_store_memories(memories)
            
            # Clear cache
            self.cache.cache.clear()
            self.cache.stats = CacheStats()
            
            # Optimize storage
            await self._optimize_storage()
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            
    async def _optimize_storage(self):
        """Optimize memory storage."""
        try:
            async with aiosqlite.connect(self.config.db_path) as db:
                # Get database stats
                cursor = await db.execute("PRAGMA page_count")
                page_count = (await cursor.fetchone())[0]
                cursor = await db.execute("PRAGMA page_size")
                page_size = (await cursor.fetchone())[0]
                
                total_size = page_count * page_size
                cursor = await db.execute("PRAGMA freelist_count")
                freelist_count = (await cursor.fetchone())[0]
                free_size = freelist_count * page_size
                
                # Vacuum if needed
                if free_size / total_size > self.config.vacuum_threshold:
                    await db.execute("VACUUM")
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")

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
                for memory in self.cache.cache.values():
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
            if len(self.cache.cache) > self.config.max_memory_size * 0.9:
                await self._consolidate_memories()
                
            # Remove low-relevance memories
            await self._cleanup_low_relevance_memories()
            
            # Compact storage
            await self._compact_storage()
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
            
    async def _consolidate_memories(self):
        """Consolidate short-term memories into long-term storage."""
        # Sort by relevance and access patterns
        memories = list(self.cache.cache.values())
        memories.sort(
            key=lambda x: (x.relevance_score, x.access_count),
            reverse=True
        )
        
        # Move most relevant memories to long-term storage
        memories_to_move = memories[:len(memories) // 2]
        
        # Update long-term memory
        for memory in memories_to_move:
            self.cache.cache.pop(memory.id)
            self.cache.cache[memory.id] = memory
            
        # Ensure long-term memory size
        if len(self.cache.cache) > self.config.max_memory_size:
            # Remove least relevant memories
            self.cache.cache.sort(
                key=lambda x: (x.relevance_score, x.access_count)
            )
            self.cache.cache = OrderedDict(
                (key, memory) for key, memory in self.cache.cache.items()
                if memory.relevance_score > self.config.relevance_threshold
            )
            
    async def _cleanup_old_memories(self):
        """Clean up old memories based on relevance and age."""
        current_time = datetime.now()
        
        # Remove old memories with low relevance
        self.cache.cache = OrderedDict(
            (key, memory) for key, memory in self.cache.cache.items()
            if (
                memory.relevance_score > self.config.relevance_threshold or
                (current_time - memory.timestamp).days < 7  # Keep recent memories
            )
        )
        
    async def _cleanup_low_relevance_memories(self):
        """Remove memories with consistently low relevance."""
        threshold = self.config.relevance_threshold / 2
        
        self.cache.cache = OrderedDict(
            (key, memory) for key, memory in self.cache.cache.items()
            if memory.relevance_score > threshold
        )
        
    async def _compact_storage(self):
        """Compact memory storage."""
        try:
            # Remove files for deleted memories
            existing_ids = set(self.cache.cache.keys())
            
            for file_path in self.config.storage_path.glob("*.json"):
                memory_id = file_path.stem
                if memory_id not in existing_ids:
                    file_path.unlink()
                    
        except Exception as e:
            logger.error(f"Storage compaction failed: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, trying each tier."""
        # Try cache
        value = await self.cache.get(key)
        if value is not None:
            return value
        
        return None
    
    async def put(self, key: str, value: Any) -> None:
        """Store value in cache system."""
        # Store in cache
        evicted = await self.cache.put(key, value)
        
        # Store evicted items in database
        if evicted:
            await self._batch_store_memories(evicted)
        
        # Always store on disk for persistence
        await self._store_memory(value)
    
    async def optimize(self) -> None:
        """Optimize cache storage."""
        await self.optimize_storage()
        
    async def _store_memory(self, memory: Memory):
        """Save memory to persistent storage."""
        try:
            file_path = self.config.storage_path / f"{memory.id}.json"
            with open(file_path, 'w') as f:
                json.dump(memory.dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save memory {memory.id}: {e}")
            
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
        self.cache.cache = OrderedDict(
            (key, memory) for key, memory in self.cache.cache.items()
            if (
                memory.relevance_score > self.config.relevance_threshold or
                (current_time - memory.timestamp).days < 7  # Keep recent memories
            )
        )
        
    async def _cleanup_low_relevance_memories(self):
        """Remove memories with consistently low relevance."""
        threshold = self.config.relevance_threshold / 2
        
        self.cache.cache = OrderedDict(
            (key, memory) for key, memory in self.cache.cache.items()
            if memory.relevance_score > threshold
        )
        
    async def _store_memory(self, memory: Memory):
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
            existing_ids = set(self.cache.cache.keys())
            
            for file_path in self.config.storage_path.glob("*.json"):
                memory_id = file_path.stem
                if memory_id not in existing_ids:
                    file_path.unlink()
                    
        except Exception as e:
            logger.error(f"Storage compaction failed: {e}")

    async def optimize(self) -> None:
        """Optimize cache storage."""
        await self.optimize_storage()
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.cache.cache.clear()
        self.cache.stats = CacheStats()
        
        await self.optimize()
        
        await self.cleanup() 
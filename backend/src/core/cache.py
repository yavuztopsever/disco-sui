"""
Caching utility for the DiscoSui application.
"""
import time
from typing import Any, Optional, Callable
from functools import wraps
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

class Cache:
    """Simple in-memory cache implementation."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            ttl: Time to live in seconds for cache entries
        """
        self.cache: dict = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
            
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
            
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        self.cache[key] = (value, time.time())
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all values from the cache."""
        self.cache.clear()

# Initialize cache
cache = Cache(ttl=settings.CACHE_TTL)

def cached(ttl: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds for the cached result
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
                
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value
                
            # If not in cache, execute function
            logger.debug(f"Cache miss for {key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache.set(key, result)
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)
                
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value
                
            # If not in cache, execute function
            logger.debug(f"Cache miss for {key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(key, result)
            return result
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache entries matching a pattern.
    
    Args:
        pattern: Pattern to match cache keys against
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Invalidate matching cache entries
            for key in list(cache.cache.keys()):
                if pattern in key:
                    cache.delete(key)
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Invalidate matching cache entries
            for key in list(cache.cache.keys()):
                if pattern in key:
                    cache.delete(key)
            return result
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 
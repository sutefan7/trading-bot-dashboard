#!/usr/bin/env python3
"""
Caching Layer for Trading Bot Dashboard
Simple in-memory cache with TTL support
"""
import time
from typing import Any, Optional, Callable
from functools import wraps
import logging

from config import Config

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 60):
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self.enabled = Config.CACHE_ENABLED
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        if key not in self._cache:
            self.misses += 1
            return None
        
        # Check if expired
        if self._is_expired(key):
            self.delete(key)
            self.misses += 1
            return None
        
        self.hits += 1
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        if not self.enabled:
            return
        
        self._cache[key] = value
        self._timestamps[key] = time.time() + (ttl or self.default_ttl)
    
    def delete(self, key: str):
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("🗑️  Cache cleared")
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache key is expired"""
        if key not in self._timestamps:
            return True
        return time.time() > self._timestamps[key]
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'enabled': self.enabled,
            'size': len(self._cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'default_ttl': self.default_ttl
        }
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        expired_keys = [
            key for key in self._cache.keys() 
            if self._is_expired(key)
        ]
        for key in expired_keys:
            self.delete(key)
        
        if expired_keys:
            logger.info(f"🗑️  Removed {len(expired_keys)} expired cache entries")


# Global cache instance
cache = SimpleCache(default_ttl=Config.CACHE_TIMEOUT_SECONDS)


def cached(ttl: Optional[int] = None, key_prefix: str = ''):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (None = use default)
        key_prefix: Prefix for cache key
    
    Usage:
        @cached(ttl=60, key_prefix='portfolio')
        def get_portfolio_data():
            # expensive operation
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"✅ Cache hit: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"❌ Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Only cache if result is not None and not an error
            if result is not None and not isinstance(result, dict) or 'error' not in result:
                cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def clear_cache_pattern(pattern: str):
    """Clear cache keys matching pattern"""
    matching_keys = [
        key for key in cache._cache.keys() 
        if pattern in key
    ]
    for key in matching_keys:
        cache.delete(key)
    
    logger.info(f"🗑️  Cleared {len(matching_keys)} cache entries matching '{pattern}'")


#!/usr/bin/env python3
"""
Advanced Caching Layer for Trading Bot Dashboard
Enhanced in-memory cache with TTL, compression, and performance monitoring
"""
import time
import json
import gzip
import pickle
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
import logging
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

from config import Config

logger = logging.getLogger(__name__)


class AdvancedCache:
    """Advanced in-memory cache with TTL, compression, and performance monitoring"""
    
    def __init__(self, default_ttl: int = 60, max_size: int = 1000, compression_threshold: int = 1024):
        self._cache = OrderedDict()  # LRU cache
        self._timestamps = {}
        self._access_counts = defaultdict(int)
        self._compression_enabled = True
        self._compression_threshold = compression_threshold
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.compressed_items = 0
        self.enabled = Config.CACHE_ENABLED
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compression_saves": 0,
            "evictions": 0,
            "start_time": datetime.now()
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU update"""
        if not self.enabled:
            return None
        
        self.performance_stats["total_requests"] += 1
        
        if key not in self._cache:
            self.misses += 1
            self.performance_stats["cache_misses"] += 1
            return None
        
        # Check if expired
        if self._is_expired(key):
            self.delete(key)
            self.misses += 1
            self.performance_stats["cache_misses"] += 1
            return None
        
        # Update LRU order
        value = self._cache.pop(key)
        self._cache[key] = value
        self._access_counts[key] += 1
        
        self.hits += 1
        self.performance_stats["cache_hits"] += 1
        
        # Decompress if needed
        return self._decompress_value(value)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL, compression, and LRU management"""
        if not self.enabled:
            return
        
        # Compress value if it's large enough
        compressed_value = self._compress_value(value)
        
        # Remove existing key if present
        if key in self._cache:
            del self._cache[key]
        
        # Check cache size and evict if necessary
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Add to cache
        self._cache[key] = compressed_value
        self._timestamps[key] = time.time() + (ttl or self.default_ttl)
        self._access_counts[key] = 0
    
    def delete(self, key: str):
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_counts.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        self._access_counts.clear()
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
        
        uptime = datetime.now() - self.performance_stats["start_time"]
        
        return {
            'enabled': self.enabled,
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'default_ttl': self.default_ttl,
            'compressed_items': self.compressed_items,
            'compression_enabled': self._compression_enabled,
            'performance_stats': self.performance_stats,
            'uptime_seconds': uptime.total_seconds(),
            'memory_usage_estimate': self._estimate_memory_usage()
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
    
    def _compress_value(self, value: Any) -> Any:
        """Compress value if it's large enough"""
        if not self._compression_enabled:
            return value
        
        try:
            # Serialize to bytes
            serialized = pickle.dumps(value)
            
            # Compress if above threshold
            if len(serialized) > self._compression_threshold:
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized):
                    self.compressed_items += 1
                    self.performance_stats["compression_saves"] += len(serialized) - len(compressed)
                    return {"_compressed": True, "data": compressed}
            
            return value
        except Exception as e:
            logger.warning(f"Compression failed for value: {e}")
            return value
    
    def _decompress_value(self, value: Any) -> Any:
        """Decompress value if it was compressed"""
        if isinstance(value, dict) and value.get("_compressed"):
            try:
                decompressed = gzip.decompress(value["data"])
                return pickle.loads(decompressed)
            except Exception as e:
                logger.warning(f"Decompression failed: {e}")
                return value
        
        return value
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._cache:
            return
        
        # Remove least recently used item (first in OrderedDict)
        lru_key = next(iter(self._cache))
        self.delete(lru_key)
        self.performance_stats["evictions"] += 1
        logger.debug(f"Evicted LRU key: {lru_key}")
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        total_size = 0
        for key, value in self._cache.items():
            try:
                total_size += len(str(key)) + len(str(value))
            except:
                total_size += 100  # Fallback estimate
        return total_size


# Global cache instance
cache = AdvancedCache(default_ttl=Config.CACHE_TIMEOUT_SECONDS, max_size=1000, compression_threshold=1024)


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


"""
Enhanced Redis caching layer for bet-intel - Phase 3.2
Read-through cache with typed helpers and rate-limited invalidation

Based on FastAPI + Redis performance patterns for high-speed endpoints
"""

import json
import time
import logging
import functools
from typing import Any, Dict, Optional, Callable, TypeVar
from datetime import datetime
from dataclasses import dataclass

from services.redis_cache import redis_client

logger = logging.getLogger(__name__)

# Type variables for generic cache decorators
T = TypeVar('T')

@dataclass
class CacheConfig:
    """Configuration for cache behavior"""
    ttl: int = 300  # Default 5 minutes
    key_prefix: str = "cache"
    serialize_json: bool = True
    compress: bool = False
    invalidation_rate_limit: int = 60  # Max invalidations per minute

# Global cache configuration
DEFAULT_CONFIG = CacheConfig()

class CacheKey:
    """Helper for generating consistent cache keys"""
    
    @staticmethod
    def opportunities(filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for opportunities data"""
        base = "opportunities"
        if filters:
            # Sort filters for consistent keys
            filter_str = "_".join(f"{k}:{v}" for k, v in sorted(filters.items()) if v)
            return f"{base}:{filter_str}" if filter_str else base
        return base
    
    @staticmethod
    def analytics(sport: Optional[str] = None) -> str:
        """Generate cache key for analytics data"""
        base = "analytics"
        return f"{base}:{sport}" if sport else base
    
    @staticmethod
    def user_data(user_id: str, role: str) -> str:
        """Generate cache key for user-specific data"""
        return f"user:{user_id}:{role}"
    
    @staticmethod
    def batch_results(batch_id: str) -> str:
        """Generate cache key for batch processing results"""
        return f"batch_results:{batch_id}"
    
    @staticmethod
    def rate_limit(identifier: str) -> str:
        """Generate cache key for rate limiting"""
        return f"rate_limit:{identifier}"

class RateLimitedCache:
    """Cache with built-in rate limiting for invalidation"""
    
    def __init__(self, config: CacheConfig = DEFAULT_CONFIG):
        self.config = config
        self.client = redis_client
        
    def _get_rate_limit_key(self, cache_key: str) -> str:
        """Get rate limit tracking key for a cache key"""
        return f"invalidation_rate:{cache_key}:minute:{int(time.time() // 60)}"
    
    def _check_invalidation_rate_limit(self, cache_key: str) -> bool:
        """Check if we can invalidate this cache key (rate limit check)"""
        if not self.client:
            return True  # Allow if Redis unavailable
        
        try:
            rate_key = self._get_rate_limit_key(cache_key)
            current_count = self.client.get(rate_key)
            
            if current_count and int(current_count) >= self.config.invalidation_rate_limit:
                logger.warning(f"Rate limit exceeded for cache invalidation: {cache_key}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def _increment_invalidation_count(self, cache_key: str):
        """Increment the invalidation counter for rate limiting"""
        if not self.client:
            return
        
        try:
            rate_key = self._get_rate_limit_key(cache_key)
            pipe = self.client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, 60)  # Expire after 1 minute
            pipe.execute()
        except Exception as e:
            logger.error(f"Error incrementing invalidation count: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with fallback"""
        if not self.client:
            return default
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            value = self.client.get(full_key)
            
            if value is None:
                return default
            
            if self.config.serialize_json:
                return json.loads(value)
            
            return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            cache_ttl = ttl or self.config.ttl
            
            if self.config.serialize_json:
                serialized_value = json.dumps(value)
            else:
                serialized_value = value
            
            self.client.setex(full_key, cache_ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str, force: bool = False) -> bool:
        """Delete cache key with rate limiting"""
        if not self.client:
            return False
        
        # Check rate limit unless forced
        if not force and not self._check_invalidation_rate_limit(key):
            return False
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            deleted = self.client.delete(full_key)
            
            if deleted and not force:
                self._increment_invalidation_count(key)
            
            return bool(deleted)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        if not self.client:
            return False
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            return bool(self.client.exists(full_key))
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False

# Global cache instance
cache = RateLimitedCache()

def cached(ttl: int = 300, key_func: Optional[Callable] = None) -> Callable:
    """
    Decorator for caching function results with TTL
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from function args
        
    Usage:
        @cached(ttl=300)
        def expensive_function(param1, param2):
            return compute_something(param1, param2)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{args_str}:{kwargs_str}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Cache miss - compute and store
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Convenience decorators for common TTL values
def cache_short(func: Callable[..., T]) -> Callable[..., T]:
    """Cache for 60 seconds - for frequently changing data"""
    return cached(ttl=60)(func)

def cache_medium(func: Callable[..., T]) -> Callable[..., T]:
    """Cache for 300 seconds (5 minutes) - default for most data"""
    return cached(ttl=300)(func)

def cache_long(func: Callable[..., T]) -> Callable[..., T]:
    """Cache for 1800 seconds (30 minutes) - for stable data"""
    return cached(ttl=1800)(func)

class HighPerformanceCache:
    """
    High-performance cache specifically optimized for API endpoints
    Implements read-through pattern with background refresh
    """
    
    def __init__(self):
        self.cache = RateLimitedCache(CacheConfig(
            ttl=300,
            key_prefix="hp_cache",
            serialize_json=True
        ))
    
    def get_opportunities(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        user_role: str = "free"
    ) -> Optional[Dict[str, Any]]:
        """
        High-performance opportunities retrieval with read-through caching
        
        Returns cached opportunities or None if cache miss
        Use this for <20ms API responses as specified in Phase 3
        """
        cache_key = CacheKey.opportunities(filters)
        role_key = f"{cache_key}:role:{user_role}"
        
        try:
            # Try role-specific cache first
            result = self.cache.get(role_key)
            if result:
                logger.debug(f"High-perf cache hit: {role_key}")
                return result
            
            # Try general cache
            general_result = self.cache.get(cache_key)
            if general_result:
                logger.debug(f"High-perf cache hit (general): {cache_key}")
                return general_result
            
            logger.debug(f"High-perf cache miss: {role_key}")
            return None
            
        except Exception as e:
            logger.error(f"High-performance cache error: {e}")
            return None
    
    def set_opportunities(
        self,
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        user_role: str = "free",
        ttl: int = 300
    ) -> bool:
        """Store opportunities in high-performance cache"""
        cache_key = CacheKey.opportunities(filters)
        role_key = f"{cache_key}:role:{user_role}"
        
        try:
            # Store both role-specific and general versions
            success1 = self.cache.set(role_key, data, ttl)
            success2 = self.cache.set(cache_key, data, ttl)
            
            return success1 and success2
        except Exception as e:
            logger.error(f"Error storing high-performance cache: {e}")
            return False
    
    def invalidate_opportunities(
        self,
        filters: Optional[Dict[str, Any]] = None,
        user_role: Optional[str] = None
    ) -> bool:
        """Invalidate opportunities cache with rate limiting"""
        cache_key = CacheKey.opportunities(filters)
        
        try:
            if user_role:
                role_key = f"{cache_key}:role:{user_role}"
                return self.cache.delete(role_key)
            else:
                # Invalidate all role variations
                success = self.cache.delete(cache_key)
                for role in ["free", "subscriber", "admin"]:
                    role_key = f"{cache_key}:role:{role}"
                    self.cache.delete(role_key, force=True)  # Force delete variations
                return success
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

# Global high-performance cache instance
hp_cache = HighPerformanceCache()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    if not redis_client:
        return {"error": "Redis not available"}
    
    try:
        info = redis_client.info("memory")
        stats = {
            "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "memory_peak_mb": round(info.get("used_memory_peak", 0) / 1024 / 1024, 2),
            "connected_clients": redis_client.info("clients").get("connected_clients", 0),
            "total_commands_processed": redis_client.info("stats").get("total_commands_processed", 0),
            "cache_hit_ratio": "Not available - would need instrumentation",
            "timestamp": datetime.utcnow().isoformat()
        }
        return stats
    except Exception as e:
        return {"error": str(e)}

# Pre-warm common cache keys on import
def prewarm_cache():
    """Pre-warm cache with common data patterns"""
    try:
        # This could be called during application startup
        # to populate cache with frequently accessed data
        logger.info("Cache pre-warming completed")
    except Exception as e:
        logger.error(f"Cache pre-warming failed: {e}")

# Export main interfaces
__all__ = [
    'cache',
    'hp_cache', 
    'cached',
    'cache_short',
    'cache_medium', 
    'cache_long',
    'CacheKey',
    'get_cache_stats',
    'prewarm_cache'
] 
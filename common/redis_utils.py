"""
Redis connection utilities
Standardizes Redis URL access and connection patterns across the application
"""

import os
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


def get_redis_url() -> str:
    """
    Get Redis URL from environment with fallback
    
    Returns:
        Redis connection URL
    """
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def create_redis_client(decode_responses: bool = True) -> aioredis.Redis:
    """
    Create a Redis client with standard configuration
    
    Args:
        decode_responses: Whether to decode byte responses to strings
        
    Returns:
        Configured Redis client
    """
    redis_url = get_redis_url()
    return aioredis.from_url(redis_url, decode_responses=decode_responses)


async def test_redis_connection() -> bool:
    """
    Test Redis connectivity
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = await create_redis_client()
        await client.ping()
        await client.close()
        return True
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False


class RedisConnectionManager:
    """
    Context manager for Redis connections with proper cleanup
    """
    
    def __init__(self, decode_responses: bool = True):
        self.decode_responses = decode_responses
        self.client: Optional[aioredis.Redis] = None
    
    async def __aenter__(self) -> aioredis.Redis:
        self.client = await create_redis_client(self.decode_responses)
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, _exc_tb):
        if self.client:
            await self.client.close()


async def safe_redis_operation(operation_func, *args, **kwargs):
    """
    Execute Redis operation with error handling
    
    Args:
        operation_func: Async function to execute
        *args, **kwargs: Arguments for the operation
        
    Returns:
        Operation result or None if failed
    """
    try:
        async with RedisConnectionManager() as redis_client:
            return await operation_func(redis_client, *args, **kwargs)
    except Exception as e:
        logger.error(f"Redis operation failed: {e}")
        return None 
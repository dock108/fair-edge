"""
Redis cache layer for bet-intel
Handles caching of EV opportunities and analytics data
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis

from core.settings import settings

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = settings.redis_url
EV_CACHE_KEY = "ev_opportunities"
ANALYTICS_CACHE_KEY = "ev_analytics"
LAST_UPDATE_KEY = "last_update"

# Initialize Redis client
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Redis connection established: {REDIS_URL}")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")
    redis_client = None


def store_ev_data(ev_list: List[Dict[str, Any]]) -> bool:
    """
    Store EV opportunities data in Redis
    Args:
        ev_list: List of EV opportunity dictionaries
    Returns:
        bool: True if successful, False otherwise
    """
    if not redis_client:
        logger.error("Redis client not available")
        return False

    try:
        # Store the opportunities data
        data_to_store = {
            "opportunities": ev_list,
            "count": len(ev_list),
            "timestamp": datetime.utcnow().isoformat(),
        }

        redis_client.set(EV_CACHE_KEY, json.dumps(data_to_store))
        redis_client.set(LAST_UPDATE_KEY, datetime.utcnow().isoformat())

        logger.info(f"✅ Stored {len(ev_list)} EV opportunities in Redis")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store EV data in Redis: {e}")
        return False


def get_ev_data() -> List[Dict[str, Any]]:
    """
    Retrieve EV opportunities data from Redis
    Returns:
        List of EV opportunity dictionaries, empty list if no data or error
    """
    if not redis_client:
        logger.error("Redis client not available")
        return []

    try:
        data = redis_client.get(EV_CACHE_KEY)
        if data:
            parsed_data = json.loads(data)
            opportunities = parsed_data.get("opportunities", [])
            logger.info(f"✅ Retrieved {len(opportunities)} EV opportunities from Redis")
            return opportunities
        else:
            logger.info("No EV data found in Redis cache")
            return []

    except Exception as e:
        logger.error(f"❌ Failed to retrieve EV data from Redis: {e}")
        return []


def store_analytics_data(analytics: Dict[str, Any]) -> bool:
    """
    Store analytics data in Redis
    Args:
        analytics: Analytics dictionary from process_opportunities
    Returns:
        bool: True if successful, False otherwise
    """
    if not redis_client:
        logger.error("Redis client not available")
        return False

    try:
        analytics_with_timestamp = {**analytics, "timestamp": datetime.utcnow().isoformat()}

        redis_client.set(ANALYTICS_CACHE_KEY, json.dumps(analytics_with_timestamp))
        logger.info("✅ Stored analytics data in Redis")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store analytics data in Redis: {e}")
        return False


def get_analytics_data() -> Dict[str, Any]:
    """
    Retrieve analytics data from Redis
    Returns:
        Analytics dictionary, empty dict if no data or error
    """
    if not redis_client:
        logger.error("Redis client not available")
        return {}

    try:
        data = redis_client.get(ANALYTICS_CACHE_KEY)
        if data:
            analytics = json.loads(data)
            logger.info("✅ Retrieved analytics data from Redis")
            return analytics
        else:
            logger.info("No analytics data found in Redis cache")
            return {}

    except Exception as e:
        logger.error(f"❌ Failed to retrieve analytics data from Redis: {e}")
        return {}


def get_last_update() -> Optional[str]:
    """
    Get the timestamp of the last data update
    Returns:
        ISO timestamp string or None if no update recorded
    """
    if not redis_client:
        return None

    try:
        return redis_client.get(LAST_UPDATE_KEY)
    except Exception as e:
        logger.error(f"❌ Failed to retrieve last update time: {e}")
        return None


def clear_cache() -> bool:
    """
    Clear all cached data
    Returns:
        bool: True if successful, False otherwise
    """
    if not redis_client:
        logger.error("Redis client not available")
        return False

    try:
        keys_to_delete = [EV_CACHE_KEY, ANALYTICS_CACHE_KEY, LAST_UPDATE_KEY]
        deleted_count = redis_client.delete(*keys_to_delete)
        logger.info(f"✅ Cleared {deleted_count} cache keys from Redis")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        return False


def health_check() -> Dict[str, Any]:
    """
    Check Redis connection and return status
    Returns:
        Dictionary with health status information
    """
    if not redis_client:
        return {
            "status": "error",
            "message": "Redis client not initialized",
            "timestamp": datetime.utcnow().isoformat(),
        }

    try:
        # Test Redis connection
        redis_client.ping()

        # Get cache status
        ev_data_exists = redis_client.exists(EV_CACHE_KEY)
        analytics_exists = redis_client.exists(ANALYTICS_CACHE_KEY)
        last_update = get_last_update()

        return {
            "status": "healthy",
            "redis_connected": True,
            "ev_data_cached": bool(ev_data_exists),
            "analytics_cached": bool(analytics_exists),
            "last_update": last_update,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "redis_connected": False,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

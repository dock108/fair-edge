"""
Cache configuration consolidated from various modules
"""

import os


class CacheConfig:
    """Cache configuration and settings"""

    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Cache durations based on environment
    CACHE_DURATION_PRODUCTION = 1800  # 30 minutes
    CACHE_DURATION_DEBUG = 10800  # 3 hours

    @property
    def cache_duration(self) -> int:
        """Get cache duration based on environment"""
        # Import here to avoid circular imports
        from . import settings

        return self.CACHE_DURATION_DEBUG if settings.is_debug else self.CACHE_DURATION_PRODUCTION

    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        from . import settings

        return settings.is_debug

    # Cache key patterns
    CACHE_KEYS = {
        "ev_data_free": "ev_opportunities:free",
        "ev_data_full": "ev_opportunities:full",
        "analytics_free": "analytics:free",
        "analytics_full": "analytics:full",
        "last_update": "last_update",
        "raw_data": "raw_data",
        "processed_data": "processed_data",
    }

    # File cache settings
    CACHE_DIR = "cache"
    RAW_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "raw_data_cache.pkl")
    PROCESSED_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "processed_data_cache.pkl")

    def get_cache_key(self, key_name: str) -> str:
        """Get a cache key by name"""
        return self.CACHE_KEYS.get(key_name, key_name)

    def get_role_cache_key(self, base_key: str, role: str) -> str:
        """Get cache key with role suffix"""
        suffix = "full" if role in ["subscriber", "admin"] else "free"
        return self.CACHE_KEYS.get(f"{base_key}_{suffix}", f"{base_key}:{suffix}")

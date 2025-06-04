"""
Unified configuration management for bet-intel application
Consolidates all configuration from scattered files
"""

from core.settings import Settings, get_settings  # Import from new location
from .sports import SportsConfig  
from .features import FeatureConfig
from .cache import CacheConfig

# Global configuration instances
settings = get_settings()  # Use the singleton function
sports_config = SportsConfig()
feature_config = FeatureConfig()
cache_config = CacheConfig()

__all__ = [
    'settings',
    'sports_config', 
    'feature_config',
    'cache_config',
    'Settings',
    'SportsConfig',
    'FeatureConfig', 
    'CacheConfig'
] 
"""
Unified configuration management for bet-intel application
Consolidates all configuration from scattered files
"""

from .settings import Settings
from .sports import SportsConfig  
from .features import FeatureConfig
from .cache import CacheConfig

# Global configuration instances
settings = Settings()
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
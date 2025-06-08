"""
Centralized configuration settings using Pydantic BaseSettings
Replaces scattered os.getenv calls throughout the application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database Configuration
    database_url: Optional[str] = None
    db_connection_string: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    # Note: If running Redis locally, configure it to save dumps in cache/ directory
    # Example: redis-server --dir ./cache/
    
    # API Configuration
    odds_api_key: Optional[str] = None
    
    # Application Configuration
    debug: bool = False
    debug_mode: bool = False
    app_env: str = "development"
    app_version: str = "unknown"
    is_debug: bool = False
    environment: str = "development"
    
    # Timing Configuration
    refresh_interval_minutes: int = 5
    
    # Logging Configuration
    log_config_path: str = "core/log_config.yaml"
    
    # Observability Configuration
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1
    
    # Security Configuration
    admin_secret: Optional[str] = None
    
    # Stripe Configuration
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app_env.lower() in ("prod", "production")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app_env.lower() in ("dev", "development")


# Global settings instance
settings = Settings()

# Backward compatibility functions
def get_redis_url() -> str:
    """Legacy function for backward compatibility"""
    return settings.redis_url

def get_database_url() -> Optional[str]:
    """Legacy function for backward compatibility"""
    return settings.database_url or settings.db_connection_string

def is_debug_mode() -> bool:
    """Legacy function for backward compatibility"""
    return settings.debug or settings.debug_mode 
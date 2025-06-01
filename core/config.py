"""
Configuration settings for bet-intel application
Centralized Pydantic settings with environment variable loading
"""
from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    odds_api_key: str
    
    # Application Configuration
    debug_mode: bool = False
    environment: str = "development"
    admin_secret: str = "dev_debug_2024"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    refresh_interval_minutes: int = 5
    
    # Supabase Configuration
    supabase_url: AnyUrl
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str  # This should be the actual JWT secret, not anon key
    db_connection_string: str
    
    # JWT Configuration
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Convert env var names to lowercase for matching
        env_prefix = ""


# Global settings instance
settings = Settings() 
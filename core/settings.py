"""
Configuration settings for bet-intel application
Centralized Pydantic settings with environment variable loading
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    supabase_url: AnyUrl
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    db_connection_string: str
    
    # Security Configuration
    # Removed unused JWT configuration - using Supabase JWT settings instead
    admin_secret: str = "CHANGE_ME"  # Will fail fast in production
    
    # Supabase JWT Configuration (used for authentication)
    supabase_jwt_algorithm: str = "HS256"  # Supabase uses HS256 with JWT secret
    
    # Application Configuration
    app_env: str = "dev"
    debug_mode: bool = False
    environment: str = "development"
    
    # API Configuration
    odds_api_key: str
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    refresh_interval_minutes: int = 5
    
    # Stripe Configuration (Optional - set defaults for development)
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_basic_price: Optional[str] = None  # $3.99/month Basic plan
    stripe_premium_price: Optional[str] = None  # $9.99/month Premium plan
    checkout_success_url: str = "http://localhost:8000/upgrade/success"
    checkout_cancel_url: str = "http://localhost:8000/pricing"
    
    # CORS Configuration
    cors_origins: str = "*"  # Will be parsed into list
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.debug_mode or self.environment == "development"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list based on environment"""
        if self.app_env == "prod":
            return [
                "https://app.betintel.com",
                "https://betintel.com"
            ]
        else:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000", 
                "http://127.0.0.1:5173",
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]
    
    @property
    def stripe_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return all([
            self.stripe_secret_key,
            self.stripe_webhook_secret,
            self.stripe_basic_price,
            self.stripe_premium_price
        ])


@lru_cache
def get_settings() -> Settings:
    """FastAPI-friendly dependency for getting settings"""
    return Settings()


# Global settings instance for backward compatibility
settings = get_settings() 
"""
Configuration settings for bet-intel application
Centralized Pydantic settings with environment variable loading
"""
from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from typing import Optional


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
    
    # Stripe Configuration (Optional - set defaults for development)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_premium_price: Optional[str] = None
    checkout_success_url: str = "http://localhost:8000/upgrade/success"
    checkout_cancel_url: str = "http://localhost:8000/pricing"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Convert env var names to lowercase for matching
        env_prefix = ""
    
    @property
    def stripe_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return all([
            self.stripe_secret_key,
            self.stripe_webhook_secret,
            self.stripe_premium_price
        ])


# Global settings instance
settings = Settings() 
"""
Main application settings consolidated from core/config.py and environment variables
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    debug_mode: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"  # Alternative debug field
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    admin_secret: str = os.getenv("ADMIN_SECRET", "change-in-production")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    
    # Database
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    db_connection_string: str = os.getenv("DB_CONNECTION_STRING", "")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # External APIs
    odds_api_key: str = os.getenv("ODDS_API_KEY", "")
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    
    # Stripe
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Application
    refresh_interval_minutes: int = int(os.getenv("REFRESH_INTERVAL_MINUTES", "5"))
    
    # Computed properties
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled (either field)"""
        return self.debug or self.debug_mode
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins based on environment"""
        if self.environment == "production":
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored instead of causing errors 
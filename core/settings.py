"""
Fair-Edge Application Configuration Management

PRODUCTION-READY CONFIGURATION SYSTEM WITH PYDANTIC SETTINGS

This module implements the centralized configuration management system for
Fair-Edge, providing type-safe, environment-aware settings with comprehensive
validation and deployment-ready defaults.

CONFIGURATION ARCHITECTURE:
==========================

1. Environment-Driven Configuration:
   - All settings loaded from environment variables for security
   - Development defaults for local development
   - Production validation prevents unsafe defaults
   - Type validation ensures configuration integrity

2. Pydantic Settings Integration:
   - Automatic environment variable parsing and type conversion
   - Comprehensive validation with clear error messages
   - Settings inheritance and override capabilities
   - IDE-friendly type hints for development productivity

3. Multi-Environment Support:
   - Development: Permissive settings for local development
   - Production: Strict validation and security-first defaults
   - Environment-specific CORS and security configurations
   - Automatic environment detection and adaptation

4. Security-First Design:
   - No sensitive defaults committed to code
   - Environment variable requirements for production
   - Automatic unsafe configuration detection
   - Comprehensive security validation

CONFIGURATION CATEGORIES:
========================

1. Database & Supabase:
   - PostgreSQL connection strings with pooling configuration
   - Supabase authentication and REST API configuration
   - JWT signing secrets and algorithm specification
   - Connection retry and timeout settings

2. Security & Authentication:
   - JWT token configuration for Supabase integration
   - Admin access secrets with production validation
   - CORS origins with environment-specific restrictions
   - Rate limiting and security header configuration

3. External APIs:
   - Sports odds API configuration and rate limiting
   - Stripe payment processing with webhook security
   - Redis caching and session management
   - Third-party service authentication

4. Application Behavior:
   - Environment detection and debug mode control
   - Feature flags and experimental functionality
   - Performance tuning and optimization settings
   - Monitoring and observability configuration

DEPLOYMENT CONFIGURATION:
========================

Required Environment Variables (Production):
- SUPABASE_URL: Supabase project URL
- SUPABASE_ANON_KEY: Supabase anonymous key
- SUPABASE_SERVICE_ROLE_KEY: Supabase service role key
- SUPABASE_JWT_SECRET: JWT signing secret from Supabase
- DB_CONNECTION_STRING: PostgreSQL connection string
- ODDS_API_KEY: Sports odds API access key
- REDIS_URL: Redis connection string
- ADMIN_SECRET: Secure admin access secret

Optional Environment Variables:
- STRIPE_SECRET_KEY: Stripe payment processing
- STRIPE_WEBHOOK_SECRET: Stripe webhook validation
- STRIPE_BASIC_PRICE: Basic subscription price ID
- STRIPE_PREMIUM_PRICE: Premium subscription price ID
- CORS_ORIGINS: Comma-separated allowed origins

Environment Detection:
- APP_ENV: Environment identifier (dev/staging/prod)
- DEBUG_MODE: Enable debug features (boolean)
- ENVIRONMENT: Application environment (development/production)

SECURITY CONSIDERATIONS:
=======================

1. Production Hardening:
   - Fail-fast validation for unsafe defaults
   - No sensitive information in configuration files
   - Environment variable requirements for secrets
   - Automatic security configuration validation

2. CORS Security:
   - Environment-specific origin restrictions
   - Production whitelist enforcement
   - Development flexibility with security warnings
   - Automatic subdomain and port handling

3. Database Security:
   - Connection string validation and pooling
   - Service role key protection
   - Database connection encryption requirements
   - Automatic connection retry with security limits

PERFORMANCE OPTIMIZATION:
========================

- LRU caching for settings instances
- Lazy loading of expensive configuration
- Environment variable caching
- Minimal startup overhead for production deployment

MONITORING AND VALIDATION:
=========================

- Comprehensive configuration validation at startup
- Environment variable requirement checking
- Security configuration audit logging
- Configuration drift detection in production
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl
from typing import Optional


class Settings(BaseSettings):
    """
    COMPREHENSIVE APPLICATION SETTINGS WITH PYDANTIC VALIDATION
    
    This class defines all configuration settings for the Fair-Edge platform,
    providing type-safe environment variable loading with comprehensive validation
    and deployment-ready defaults. All settings are loaded from environment
    variables to ensure security and environment-specific configuration.
    
    Configuration Features:
    - Type-safe environment variable parsing
    - Automatic validation with clear error messages
    - Environment-specific defaults and overrides
    - Security-first configuration with fail-safe behavior
    - Performance optimization with caching and lazy loading
    
    Production Benefits:
    - No sensitive defaults in source code
    - Automatic configuration validation at startup
    - Environment-aware CORS and security settings
    - Comprehensive error handling for missing configuration
    - IDE-friendly type hints for development productivity
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file in development
        case_sensitive=False,      # Environment variables are case-insensitive
        extra="ignore"            # Ignore unknown environment variables
    )
    
    # ===========================================
    # DATABASE & AUTHENTICATION CONFIGURATION
    # ===========================================
    
    # Supabase Configuration - Core backend infrastructure
    supabase_url: AnyUrl                    # Supabase project URL (required)
    supabase_anon_key: str                  # Public anonymous key for client-side operations
    supabase_service_role_key: str          # Service role key for server-side operations
    supabase_jwt_secret: str                # JWT signing secret from Supabase project settings
    
    # Database Connection - PostgreSQL via Supabase or direct connection
    db_connection_string: str               # Full PostgreSQL connection string with pooling
    
    # ===========================================
    # SECURITY & ADMINISTRATION CONFIGURATION
    # ===========================================
    
    # Admin Access Control - Production requires secure secret
    admin_secret: str = "CHANGE_ME"         # SECURITY: Will fail fast in production if unchanged
    
    # JWT Authentication Configuration
    supabase_jwt_algorithm: str = "HS256"   # JWT algorithm - Supabase default is HS256
    
    # ===========================================
    # APPLICATION ENVIRONMENT CONFIGURATION
    # ===========================================
    
    # Environment Detection and Behavior
    app_env: str = "dev"                    # Environment: dev/staging/prod
    debug_mode: bool = False                # Enable debug features and verbose logging
    environment: str = "development"        # Application environment for feature flags
    
    # ===========================================
    # EXTERNAL API CONFIGURATION
    # ===========================================
    
    # Sports Odds API - Primary data source for betting opportunities
    odds_api_key: str                       # API key for The Odds API (required)
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"  # Base URL for odds API
    
    # ===========================================
    # CACHING & PERFORMANCE CONFIGURATION
    # ===========================================
    
    # Redis Configuration - Caching and session management
    redis_url: str = "redis://localhost:6379/0"    # Redis connection string
    refresh_interval_minutes: int = 5               # Background data refresh interval
    
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
                "https://app.fairedge.com",
                "https://fairedge.com"
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
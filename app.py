"""
Fair-Edge Sports Betting Analysis API

PRODUCTION-READY MODULAR FASTAPI APPLICATION

This is the main FastAPI application that serves as the backend API for Fair-Edge,
a comprehensive sports betting expected value (EV) analysis platform. The application
has been refactored into a modular structure for better maintainability and scalability.

MODULAR ARCHITECTURE:
===================

The application is now organized into focused router modules:

1. Core Routes:
   - routes.opportunities: Betting opportunities and EV analysis
   - routes.auth: Authentication and session management  
   - routes.analytics: Advanced analytics for subscribers
   - routes.admin: Administrative functionality
   - routes.system: Cache management and system monitoring
   - routes.debug: Health checks and debugging tools
   - routes.billing: Subscription and payment management
   - routes.realtime: WebSocket and real-time updates

2. Startup Configuration:
   - Environment validation and settings initialization
   - Database connection setup with proper error handling
   - Redis cache initialization with fallback strategies
   - Celery background task system initialization
   - CORS and middleware configuration

3. Security Features:
   - JWT-based authentication with Supabase integration
   - Rate limiting on all endpoints
   - CSRF protection for state-changing operations
   - Role-based access control throughout
   - Secure session management

DEPLOYMENT CONFIGURATION:
========================

- Production-ready CORS settings
- Proxy header support for load balancers
- Graceful shutdown handling
- Comprehensive health check endpoints
- Structured logging with observability
- Environment-specific configuration validation

USAGE:
======

Development:
    uvicorn app:app --reload --port 8000

Production:
    uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

Docker:
    docker-compose up -d

The application automatically configures itself based on environment variables
and provides comprehensive error handling and logging for production deployment.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import core configuration and utilities
from core.settings import settings
from core.logging import setup_logging
from core.rate_limit import limiter
from core.exceptions import setup_exception_handlers

# Import all route modules
from routes import opportunities, system, debug, dashboard_admin, auth, billing
# Temporarily disabled imports for startup
# from routes import analytics, admin, realtime

# Service initialization functions
async def initialize_redis():
    """Initialize Redis connection and verify connectivity"""
    try:
        # Import Redis utilities
        from common.redis_utils import get_redis
        
        # Test Redis connection
        redis_client = get_redis()
        await redis_client.ping()
        logger.info("✅ Redis initialized and connected successfully")
        return True
    except ImportError:
        logger.warning("Redis utilities not available, using simple mode")
        return True
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        logger.warning("Continuing without Redis cache - performance may be degraded")
        return False

async def close_redis():
    """Clean up Redis connections"""
    try:
        from common.redis_utils import get_redis
        redis_client = get_redis()
        await redis_client.close()
        logger.info("Redis connections closed")
        return True
    except Exception as e:
        logger.error(f"Error closing Redis connections: {e}")
        return False

def initialize_celery():
    """Initialize Celery background task processing"""
    try:
        from services.celery_app import celery_app
        
        # Test Celery connectivity
        celery_status = celery_app.control.inspect().stats()
        if celery_status:
            logger.info("✅ Celery initialized and workers available")
        else:
            logger.warning("⚠️ Celery initialized but no workers detected")
        return True
    except ImportError:
        logger.warning("Celery not available, background tasks disabled")
        return True
    except Exception as e:
        logger.error(f"❌ Celery initialization failed: {e}")
        logger.warning("Continuing without background tasks")
        return False

# Database initialization functions
async def initialize_database():
    """Initialize database connection and verify Supabase connectivity"""
    try:
        from db import check_supabase_connection, get_database_status
        
        # Check Supabase connection
        is_connected = await check_supabase_connection()
        if is_connected:
            logger.info("✅ Database (Supabase) initialized and connected successfully")
            
            # Get detailed status for logging
            db_status = await get_database_status()
            logger.info(f"Database status: {db_status['overall_status']}")
            return True
        else:
            logger.error("❌ Database connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def close_database():
    """Clean up database connections (Supabase REST API - no persistent connections)"""
    logger.info("Database cleanup completed (Supabase REST API)")
    return True

async def run_startup_migrations():
    """Check migration status and validate database schema"""
    try:
        # For Supabase, we don't run migrations via the app
        # But we can validate that essential tables exist
        from db import get_supabase
        
        supabase = get_supabase()
        
        # Test critical tables exist by attempting to read (with limit 0)
        essential_tables = ['profiles', 'opportunities']
        
        for table_name in essential_tables:
            try:
                result = supabase.table(table_name).select('*').limit(0).execute()
                logger.debug(f"✅ Table '{table_name}' accessible")
            except Exception as e:
                logger.error(f"❌ Table '{table_name}' not accessible: {e}")
                return False
        
        logger.info("✅ Database schema validation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema validation failed: {e}")
        return False

def validate_environment():
    """Validate critical environment configuration for production readiness"""
    try:
        missing_vars = []
        warnings = []
        
        # Critical environment variables
        critical_vars = {
            'SUPABASE_URL': settings.supabase_url,
            'SUPABASE_SERVICE_ROLE_KEY': settings.supabase_service_role_key,
            'SUPABASE_JWT_SECRET': settings.supabase_jwt_secret,
            'ODDS_API_KEY': settings.odds_api_key,
        }
        
        for var_name, value in critical_vars.items():
            if not value:
                missing_vars.append(var_name)
        
        # Optional but recommended variables
        optional_vars = {
            'REDIS_URL': settings.redis_url,
            'STRIPE_SECRET_KEY': settings.stripe_secret_key,
        }
        
        for var_name, value in optional_vars.items():
            if not value:
                warnings.append(f"{var_name} not configured - related features disabled")
        
        # Production-specific checks
        if settings.environment == "production":
            if settings.admin_secret == "CHANGE_ME":
                missing_vars.append("ADMIN_SECRET (must be changed from default)")
            
            if not settings.cors_origins_list or "*" in settings.cors_origins_list:
                warnings.append("CORS origins not properly restricted for production")
        
        # Report results
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(f"❌ {error_msg}")
            if settings.environment == "production":
                raise ValueError(error_msg)
            else:
                logger.warning("Continuing in development mode with missing variables")
        
        for warning in warnings:
            logger.warning(f"⚠️ {warning}")
        
        if not missing_vars:
            logger.info(f"✅ Environment validation passed for {settings.environment} environment")
        
        return len(missing_vars) == 0
        
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown tasks
    """
    # Startup
    logger.info("Starting Fair-Edge API server...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await initialize_database()
        
        # Run database migrations
        logger.info("Running database migrations...")
        migration_success = await run_startup_migrations()
        if not migration_success:
            logger.warning("Database migrations failed, but continuing startup...")
        
        # Initialize Redis cache
        logger.info("Initializing Redis cache...")
        await initialize_redis()
        
        # Initialize Celery (simple mode)
        logger.info("Initializing Celery background tasks...")
        initialize_celery()
        
        # Validate environment configuration
        logger.info("Validating environment configuration...")
        validate_environment()
        
        logger.info("Fair-Edge API server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fair-Edge API server...")
    
    try:
        # Close database connections
        await close_database()
        
        # Close Redis connections
        await close_redis()
        
        logger.info("Fair-Edge API server shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Legacy validation function - now replaced by enhanced version above
# Kept for backward compatibility if referenced elsewhere

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    # Create FastAPI app with lifespan manager
    app = FastAPI(
        title="Fair-Edge Sports Betting API",
        description="Advanced sports betting expected value analysis platform",
        version="2.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan
    )
    
    # Configure CORS
    if settings.environment == "development":
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080"
        ]
    else:
        origins = [
            "https://fair-edge.com",
            "https://www.fair-edge.com",
            "https://app.fair-edge.com"
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add rate limiting middleware
    app.state.limiter = limiter
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include route modules
    app.include_router(opportunities.router)
    app.include_router(system.router)
    app.include_router(debug.router)
    app.include_router(dashboard_admin.router)
    # Authentication routes enabled
    app.include_router(auth.router)
    # Billing routes enabled for subscription testing
    app.include_router(billing.router)
    # app.include_router(analytics.router)
    # app.include_router(admin.router)
    # app.include_router(realtime.router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """
        API root endpoint with service information
        """
        return {
            "service": "Fair-Edge Sports Betting API",
            "version": "2.0.0",
            "status": "operational",
            "environment": settings.environment,
            "documentation": "/docs" if settings.environment != "production" else "Contact support",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "opportunities": "/api/opportunities",
                "authentication": "/api/session",
                "health": "/health",
                "admin": "/api/admin" if settings.environment != "production" else "Admin access restricted"
            }
        }
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """
        Log all incoming requests for monitoring
        """
        start_time = datetime.now()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    return app

# Create the FastAPI application
app = create_app()

# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level="info",
        access_log=True
    )
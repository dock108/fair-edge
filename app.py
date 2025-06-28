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
from routes import opportunities, auth, analytics, admin, system, debug, billing, realtime, dashboard_admin

# Import services for startup/shutdown
from services.redis_cache import initialize_redis, close_redis
from services.celery_app import initialize_celery
from db import initialize_database, close_database
from utils.migrations import run_startup_migrations

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
        
        # Initialize Celery (if enabled)
        if settings.enable_background_tasks:
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

def validate_environment():
    """
    Validate critical environment configuration
    Fail fast if production requirements are not met
    """
    if settings.environment == "production":
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "JWT_SECRET_KEY",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables for production: {missing_vars}")
        
        # Check for unsafe defaults
        if os.getenv("JWT_SECRET_KEY") == "your-secret-key-here":
            raise ValueError("JWT_SECRET_KEY must be changed from default value in production")
    
    logger.info(f"Environment validation passed for {settings.environment} environment")

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
    
    # Include all route modules
    app.include_router(opportunities.router)
    app.include_router(auth.router)
    app.include_router(analytics.router)
    app.include_router(admin.router)
    app.include_router(system.router)
    app.include_router(debug.router)
    app.include_router(billing.router)
    app.include_router(realtime.router)
    app.include_router(dashboard_admin.router)
    
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
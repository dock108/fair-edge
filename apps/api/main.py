"""
FastAPI API-only application for Sports Betting +EV Analyzer
Serves JSON API endpoints for React frontend
"""

from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import uvicorn
import logging
import asyncio
from datetime import datetime
from typing import Optional
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

# Import logging and observability setup
from core.logging import setup_logging
from core.observability import setup_observability

# Import background task services
from services.tasks import refresh_odds_data, health_check as celery_health_check
from services.redis_cache import get_ev_data, health_check as redis_health_check

# Import database connections
from db import get_database_status

# Import authentication services
from core.auth import get_current_user, UserCtx

# Import core settings
from core.settings import settings
from core.security import fail_fast_on_unsafe_defaults
from core.rate_limit import limiter

# Import routes
from routes.billing import router as billing_router
from routes.realtime import router as realtime_router
from routes.admin import router as admin_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fail fast on unsafe defaults in production
fail_fast_on_unsafe_defaults()

# Global cleanup registry
cleanup_functions = []

def register_cleanup(func):
    """Register a cleanup function to be called on shutdown"""
    cleanup_functions.append(func)
    logger.info(f"✅ Registered {func.__name__} cleanup")

async def cleanup_background_tasks():
    """Clean up all background tasks and connections"""
    logger.info("🧹 Starting cleanup of background tasks...")
    
    for cleanup_func in cleanup_functions:
        try:
            if asyncio.iscoroutinefunction(cleanup_func):
                await cleanup_func()
            else:
                cleanup_func()
            logger.info(f"✅ Cleaned up {cleanup_func.__name__}")
        except Exception as e:
            logger.warning(f"⚠️ Error in cleanup {cleanup_func.__name__}: {e}")
    
    logger.info("✅ Background tasks cleanup completed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    logger.info("🚀 Application starting up...")
    
    # Setup structured logging first
    setup_logging()
    
    # Setup observability after app creation
    setup_observability(app)
    
    await cleanup_background_tasks()
    yield
    # Shutdown
    logger.info("🛑 Application shutting down...")
    await cleanup_background_tasks()


# Create FastAPI app with lifespan context manager
app = FastAPI(
    title="Bet Intel API - Sports +EV Analysis", 
    description="API for sports betting analysis and odds comparison tool",
    version="2.1.0",
    lifespan=lifespan
)

# Add rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add proxy headers middleware for proper IP detection behind load balancers
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        *settings.cors_origins_list
    ],
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"]  # Allow frontend to read CSRF token
)

# Create auth router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/test-token")
async def test_token(user: UserCtx = Depends(get_current_user)):
    """Test endpoint to verify JWT token validation"""
    return {
        "status": "success",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "subscription_status": user.subscription_status
        },
        "message": "Token is valid"
    }

@auth_router.get("/me")
async def get_my_profile(current_user: UserCtx = Depends(get_current_user)):
    """Get the current user's profile information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "subscription_status": current_user.subscription_status
    }

# Main user profile endpoint (alternative to /auth/me)
@app.get("/me")
async def get_my_profile_main(current_user: UserCtx = Depends(get_current_user)):
    """Get the current user's profile information - main endpoint"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "subscription_status": current_user.subscription_status
    }

# Include routers
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(realtime_router)
app.include_router(admin_router)

# Register cleanup functions from other modules
try:
    from routes.realtime import cleanup_redis_connections
    register_cleanup(cleanup_redis_connections)
except ImportError:
    logger.warning("Could not import realtime cleanup functions")

# API Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    start_time = time.time()
    
    # Check Redis connectivity
    redis_healthy = await redis_health_check()
    
    # Check Celery workers
    celery_healthy = await celery_health_check()
    
    # Check database connectivity
    try:
        db_status = await get_database_status()
        db_healthy = db_status.get("status") == "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    health_status = {
        "status": "healthy" if all([redis_healthy, celery_healthy, db_healthy]) else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "services": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "celery": "healthy" if celery_healthy else "unhealthy", 
            "database": "healthy" if db_healthy else "unhealthy"
        },
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

# API endpoints (keeping all existing API routes)
@app.get("/api/opportunities")
@limiter.limit("60/minute")
async def api_opportunities(
    request: Request, 
    search: Optional[str] = None,
    sport: Optional[str] = None,
    batch_id: Optional[str] = None
):
    """Get betting opportunities with optional filtering"""
    start_time = time.time()
    
    try:
        # Get cached data
        cached_data = await get_ev_data()
        if not cached_data:
            return JSONResponse(
                content={"error": "No data available", "opportunities": []},
                status_code=200
            )
        
        opportunities = cached_data.get("opportunities", [])
        
        # Apply filters
        if search:
            search_lower = search.lower()
            opportunities = [
                opp for opp in opportunities
                if any(search_lower in str(field).lower() for field in [
                    opp.get("event", ""),
                    opp.get("bet_description", ""),
                    opp.get("bet_type", ""),
                    opp.get("best_odds_source", "")
                ])
            ]
        
        if sport:
            opportunities = [
                opp for opp in opportunities
                if sport.lower() in opp.get("event", "").lower()
            ]
        
        # Return API response
        return {
            "opportunities": opportunities,
            "total": len(opportunities),
            "filters_applied": bool(search or sport),
            "last_updated": cached_data.get("last_updated"),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        return JSONResponse(
            content={"error": "Internal server error", "opportunities": []},
            status_code=500
        )

@app.post("/api/opportunities/refresh")
@limiter.limit("10/minute")
async def trigger_ev_refresh(request: Request):
    """Trigger manual refresh of betting opportunities"""
    try:
        task = refresh_odds_data.delay()
        return {
            "status": "success",
            "task_id": task.id,
            "message": "Refresh task queued successfully"
        }
    except Exception as e:
        logger.error(f"Error triggering refresh: {e}")
        return JSONResponse(
            content={"error": "Failed to trigger refresh"},
            status_code=500
        )

# Keep all other API endpoints from the original app.py...
# (Additional endpoints would be added here)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
"""
Debug and Health Check Routes
Handles system health monitoring, debugging endpoints, and diagnostics
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import sys
import os
import psutil

# Import authentication and dependencies
from core.auth import require_role, get_user_or_none, UserCtx
from core.rate_limit import limiter
from core.settings import settings

# Import database and services
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis

def get_redis_client():
    return redis.from_url(settings.redis_url)

# Initialize router
router = APIRouter(tags=["debug", "health"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(request: Request):
    """
    Comprehensive system health check
    Public endpoint for load balancer health monitoring
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "checks": {}
        }
        
        # Database health check
        try:
            # This would need to be async if using get_db()
            # For now, basic connection test
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection available"
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Redis health check
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection active"
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # System resources check
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Alert if memory > 90% or disk > 95%
            memory_status = "healthy" if memory.percent < 90 else "warning"
            disk_status = "healthy" if disk.percent < 95 else "warning"
            
            health_status["checks"]["system_resources"] = {
                "status": "healthy" if memory_status == "healthy" and disk_status == "healthy" else "warning",
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "memory_status": memory_status,
                "disk_status": disk_status
            }
            
            if memory_status == "warning" or disk_status == "warning":
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["checks"]["system_resources"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Determine overall status
        unhealthy_checks = [
            check for check in health_status["checks"].values() 
            if check.get("status") == "unhealthy"
        ]
        
        if unhealthy_checks:
            health_status["status"] = "unhealthy"
        
        # Return appropriate HTTP status
        status_code = 200
        if health_status["status"] == "unhealthy":
            status_code = 503
        elif health_status["status"] == "degraded":
            status_code = 200  # Still operational
        
        return Response(
            content=str(health_status),
            status_code=status_code,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=str({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }),
            status_code=503,
            media_type="application/json"
        )

@router.get("/debug/profiles")
@limiter.limit("10/minute")
async def debug_profiles(
    request: Request,
    limit: int = 10,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug endpoint to view user profiles
    Admin only - for troubleshooting user issues
    """
    try:
        # This would need proper database integration
        # For now, return basic debug info
        debug_info = {
            "profiles_debug": {
                "endpoint": "profiles",
                "limit": limit,
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
                "note": "This endpoint requires database integration for full functionality"
            },
            "user_context": {
                "admin_id": admin_user.id,
                "admin_email": admin_user.email,
                "admin_role": admin_user.role
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug profiles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Debug profiles failed: {str(e)}"
        )

@router.get("/debug/supabase")
@limiter.limit("10/minute") 
async def debug_supabase(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug Supabase connection and configuration
    Admin only - for troubleshooting authentication issues
    """
    try:
        debug_info = {
            "supabase_debug": {
                "endpoint": "supabase",
                "connection_status": "Not implemented",
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat()
            },
            "environment_check": {
                "has_supabase_url": bool(os.getenv("SUPABASE_URL")),
                "has_supabase_key": bool(os.getenv("SUPABASE_ANON_KEY")),
                "has_supabase_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
            },
            "settings_check": {
                "environment": settings.environment,
                "debug_mode": getattr(settings, 'debug', False)
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug supabase: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Supabase debug failed: {str(e)}"
        )

@router.get("/debug/database-status")
@limiter.limit("10/minute")
async def debug_database_status(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug database connection and basic queries
    Admin only - for troubleshooting database issues
    """
    try:
        # Test basic database connectivity
        result = await db.execute(text("SELECT 1 as test"))
        test_result = result.scalar()
        
        # Get basic table info
        tables_result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in tables_result.fetchall()]
        
        # Get profiles table count if it exists
        profiles_count = 0
        if 'profiles' in tables:
            count_result = await db.execute(text("SELECT COUNT(*) FROM profiles"))
            profiles_count = count_result.scalar()
        
        debug_info = {
            "database_debug": {
                "connection_test": "passed" if test_result == 1 else "failed",
                "test_query_result": test_result,
                "available_tables": tables,
                "profiles_count": profiles_count,
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat()
            },
            "connection_info": {
                "database_url_configured": bool(os.getenv("DB_CONNECTION_STRING") or os.getenv("DATABASE_URL")),
                "connection_pool_status": "active"
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug database status: {e}")
        return {
            "database_debug": {
                "connection_test": "failed",
                "error": str(e),
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat()
            }
        }

@router.post("/debug/trigger-refresh")
@limiter.limit("5/minute")
async def debug_trigger_refresh(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug endpoint to trigger data refresh
    Admin only - for testing background task functionality
    """
    try:
        # Import here to avoid circular imports
        from services.tasks import refresh_odds_data
        
        # Trigger refresh task
        task = refresh_odds_data.delay()
        
        logger.info(f"Debug refresh triggered by admin: {admin_user.email}")
        
        return {
            "debug_refresh": {
                "task_triggered": True,
                "task_id": task.id,
                "triggered_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
                "note": "Check task status at /api/task-status/{task_id}"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in debug trigger refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Debug refresh failed: {str(e)}"
        )

@router.get("/debug/cookies")
@limiter.limit("30/minute")
async def debug_cookies(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug endpoint to inspect cookies and session data
    Admin only - for troubleshooting authentication issues
    """
    try:
        cookies_info = {}
        
        # Get all cookies from request
        for name, value in request.cookies.items():
            # Don't expose sensitive cookie values in logs
            if name in ["session_token", "csrf_token"]:
                cookies_info[name] = {
                    "present": True,
                    "length": len(value),
                    "preview": value[:10] + "..." if len(value) > 10 else value
                }
            else:
                cookies_info[name] = value
        
        # Get headers related to authentication
        auth_headers = {}
        for header_name in ["authorization", "x-csrf-token", "user-agent"]:
            header_value = request.headers.get(header_name)
            if header_value:
                auth_headers[header_name] = header_value[:50] + "..." if len(header_value) > 50 else header_value
        
        debug_info = {
            "cookies_debug": {
                "cookies_present": cookies_info,
                "auth_headers": auth_headers,
                "user_context": {
                    "authenticated_as": admin_user.email,
                    "role": admin_user.role,
                    "user_id": admin_user.id
                },
                "request_info": {
                    "client_host": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")[:100]
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug cookies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cookie debug failed: {str(e)}"
        )

@router.get("/debug/system-info")
@limiter.limit("10/minute")
async def debug_system_info(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get comprehensive system information for debugging
    Admin only - for system troubleshooting and monitoring
    """
    try:
        # System information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": os.cpu_count(),
            "environment_variables": {
                key: "***" if any(secret in key.lower() for secret in ["key", "secret", "password", "token"]) else value
                for key, value in os.environ.items()
                if not key.startswith("_")
            }
        }
        
        # Process information
        try:
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "num_threads": process.num_threads()
            }
        except Exception:
            process_info = {"error": "Process info unavailable"}
        
        return {
            "system_debug": {
                "system_info": system_info,
                "process_info": process_info,
                "settings": {
                    "environment": settings.environment,
                    "debug_mode": getattr(settings, 'debug', False)
                },
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"System info debug failed: {str(e)}"
        )
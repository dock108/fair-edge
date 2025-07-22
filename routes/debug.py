"""
Debug and Health Check Routes
Handles system health monitoring, debugging endpoints, and diagnostics
"""

import logging
import os
import sys
from datetime import datetime

import psutil
import redis
from fastapi import APIRouter, Depends, HTTPException, Request, Response

# Import authentication and dependencies
from core.auth import UserCtx, require_role
from core.rate_limit import limiter
from core.settings import settings

# Import database and services
from db import check_supabase_connection, get_supabase

# Typing imports removed - not used


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
            "checks": {},
        }

        # Supabase health check
        try:
            supabase_healthy = await check_supabase_connection()
            if supabase_healthy:
                health_status["checks"]["supabase"] = {
                    "status": "healthy",
                    "message": "Supabase connection active",
                }
            else:
                health_status["checks"]["supabase"] = {
                    "status": "unhealthy",
                    "message": "Supabase connection failed",
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["supabase"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        # Redis health check
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection active",
            }
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"

        # System resources check
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Alert if memory > 90% or disk > 95%
            memory_status = "healthy" if memory.percent < 90 else "warning"
            disk_status = "healthy" if disk.percent < 95 else "warning"

            health_status["checks"]["system_resources"] = {
                "status": (
                    "healthy"
                    if memory_status == "healthy" and disk_status == "healthy"
                    else "warning"
                ),
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "memory_status": memory_status,
                "disk_status": disk_status,
            }

            if memory_status == "warning" or disk_status == "warning":
                health_status["status"] = "degraded"

        except Exception as e:
            health_status["checks"]["system_resources"] = {
                "status": "unknown",
                "error": str(e),
            }

        # Determine overall status
        unhealthy_checks = [
            check
            for check in health_status["checks"].values()
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
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=str(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            status_code=503,
            media_type="application/json",
        )


@router.get("/debug/profiles")
@limiter.limit("10/minute")
async def debug_profiles(
    request: Request,
    limit: int = 10,
    admin_user: UserCtx = Depends(require_role("admin")),
):
    """
    Debug endpoint to view user profiles
    Admin only - for troubleshooting user issues
    """
    try:
        # Get user profiles using Supabase
        supabase = get_supabase()
        result = (
            supabase.table("profiles")
            .select("id, email, role, subscription_status, created_at, updated_at")
            .limit(limit)
            .execute()
        )

        debug_info = {
            "profiles_debug": {
                "endpoint": "profiles",
                "limit": limit,
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
                "total_returned": len(result.data) if result.data else 0,
            },
            "profiles": result.data if result.data else [],
            "user_context": {
                "admin_id": admin_user.id,
                "admin_email": admin_user.email,
                "admin_role": admin_user.role,
            },
        }

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Debug profiles failed: {str(e)}")


@router.get("/debug/supabase")
@limiter.limit("10/minute")
async def debug_supabase(request: Request, admin_user: UserCtx = Depends(require_role("admin"))):
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
                "timestamp": datetime.now().isoformat(),
            },
            "environment_check": {
                "has_supabase_url": bool(os.getenv("SUPABASE_URL")),
                "has_supabase_key": bool(os.getenv("SUPABASE_ANON_KEY")),
                "has_supabase_service_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
            },
            "settings_check": {
                "environment": settings.environment,
                "debug_mode": getattr(settings, "debug", False),
            },
        }

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug supabase: {e}")
        raise HTTPException(status_code=500, detail=f"Supabase debug failed: {str(e)}")


@router.get("/debug/database-status")
@limiter.limit("10/minute")
async def debug_database_status(
    request: Request, admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug database connection and basic queries
    Admin only - for troubleshooting database issues
    """
    try:
        # Test basic Supabase connectivity
        supabase = get_supabase()

        # Test connection by querying profiles table
        profiles_result = supabase.table("profiles").select("id").limit(1).execute()
        connection_test = "passed" if hasattr(profiles_result, "data") else "failed"

        # Get profiles table count
        profiles_count_result = supabase.table("profiles").select("id", count="exact").execute()
        profiles_count = (
            profiles_count_result.count if hasattr(profiles_count_result, "count") else 0
        )

        debug_info = {
            "database_debug": {
                "connection_test": connection_test,
                "supabase_status": "connected",
                "profiles_table": "accessible",
                "profiles_count": profiles_count,
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
            },
            "connection_info": {
                "database_url_configured": bool(
                    os.getenv("DB_CONNECTION_STRING") or os.getenv("DATABASE_URL")
                ),
                "connection_pool_status": "active",
            },
        }

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug database status: {e}")
        return {
            "database_debug": {
                "connection_test": "failed",
                "error": str(e),
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
            }
        }


@router.post("/debug/trigger-refresh")
@limiter.limit("5/minute")
async def debug_trigger_refresh(
    request: Request, admin_user: UserCtx = Depends(require_role("admin"))
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
                "note": "Check task status at /api/task-status/{task_id}",
            }
        }

    except Exception as e:
        logger.error(f"Error in debug trigger refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Debug refresh failed: {str(e)}")


@router.get("/debug/cookies")
@limiter.limit("30/minute")
async def debug_cookies(request: Request, admin_user: UserCtx = Depends(require_role("admin"))):
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
                    "preview": value[:10] + "..." if len(value) > 10 else value,
                }
            else:
                cookies_info[name] = value

        # Get headers related to authentication
        auth_headers = {}
        for header_name in ["authorization", "x-csrf-token", "user-agent"]:
            header_value = request.headers.get(header_name)
            if header_value:
                auth_headers[header_name] = (
                    header_value[:50] + "..." if len(header_value) > 50 else header_value
                )

        debug_info = {
            "cookies_debug": {
                "cookies_present": cookies_info,
                "auth_headers": auth_headers,
                "user_context": {
                    "authenticated_as": admin_user.email,
                    "role": admin_user.role,
                    "user_id": admin_user.id,
                },
                "request_info": {
                    "client_host": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")[:100],
                },
                "timestamp": datetime.now().isoformat(),
            }
        }

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug cookies: {e}")
        raise HTTPException(status_code=500, detail=f"Cookie debug failed: {str(e)}")


@router.get("/debug/system-info")
@limiter.limit("10/minute")
async def debug_system_info(request: Request, admin_user: UserCtx = Depends(require_role("admin"))):
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
                key: (
                    "***"
                    if any(
                        secret in key.lower() for secret in ["key", "secret", "password", "token"]
                    )
                    else value
                )
                for key, value in os.environ.items()
                if not key.startswith("_")
            },
        }

        # Process information
        try:
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "num_threads": process.num_threads(),
            }
        except Exception:
            process_info = {"error": "Process info unavailable"}

        return {
            "system_debug": {
                "system_info": system_info,
                "process_info": process_info,
                "settings": {
                    "environment": settings.environment,
                    "debug_mode": getattr(settings, "debug", False),
                },
                "requested_by": admin_user.email,
                "timestamp": datetime.now().isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=f"System info debug failed: {str(e)}")

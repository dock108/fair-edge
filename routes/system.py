"""
System Management Routes
Handles cache management, background tasks, and system monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import asyncio

# Import authentication and dependencies
from core.auth import require_role, UserCtx
from core.rate_limit import limiter
from core.session import require_csrf_validation

# Import services
from services.redis_cache import clear_cache, health_check
from services.tasks import refresh_odds_data
from services.celery_app import celery_app
import redis
from core.settings import settings

# Simple helper functions
def get_redis_client():
    return redis.from_url(settings.redis_url)

def get_cache_info():
    try:
        client = get_redis_client()
        info = client.info()
        return {
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "keyspace": info.get("db0", "{}"),
            "status": "connected"
        }
    except:
        return {"status": "error", "message": "Could not connect to Redis"}

def clear_all_cache():
    try:
        client = get_redis_client()
        client.flushall()
        return {"success": True}
    except:
        return {"success": False}

def get_task_status(task_id):
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }
    except:
        return {"task_id": task_id, "status": "unknown"}

# Initialize router
router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)

@router.get("/api/cache-status", tags=["system"])
@limiter.limit("30/minute")
async def get_cache_status(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get Redis cache status and statistics
    Admin only endpoint for system monitoring
    """
    try:
        cache_info = get_cache_info()
        
        # Get Redis client for additional stats
        redis_client = get_redis_client()
        redis_info = redis_client.info()
        
        # Get key statistics
        key_pattern_stats = {}
        for pattern in ['ev_data*', 'analytics*', 'session*', 'rate_limit*']:
            try:
                keys = redis_client.keys(pattern)
                key_pattern_stats[pattern] = len(keys)
            except Exception as e:
                key_pattern_stats[pattern] = f"Error: {e}"
        
        return {
            "cache_status": "connected",
            "cache_info": cache_info,
            "redis_stats": {
                "connected_clients": redis_info.get('connected_clients', 0),
                "used_memory_human": redis_info.get('used_memory_human', 'Unknown'),
                "used_memory_peak_human": redis_info.get('used_memory_peak_human', 'Unknown'),
                "total_commands_processed": redis_info.get('total_commands_processed', 0),
                "uptime_in_seconds": redis_info.get('uptime_in_seconds', 0),
                "keyspace_hits": redis_info.get('keyspace_hits', 0),
                "keyspace_misses": redis_info.get('keyspace_misses', 0)
            },
            "key_statistics": key_pattern_stats,
            "cache_hit_ratio": (
                redis_info.get('keyspace_hits', 0) / 
                max(redis_info.get('keyspace_hits', 0) + redis_info.get('keyspace_misses', 0), 1)
            ) * 100,
            "checked_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache status: {str(e)}"
        )

@router.post("/api/clear-cache", tags=["system"])
@limiter.limit("5/minute")
async def clear_cache(
    request: Request,
    cache_type: Optional[str] = "all",
    admin_user: UserCtx = Depends(require_role("admin")),
    _csrf_valid: bool = Depends(require_csrf_validation)
):
    """
    Clear Redis cache with optional type filtering
    Admin only endpoint with CSRF protection
    """
    try:
        redis_client = get_redis_client()
        cleared_keys = 0
        
        if cache_type == "all":
            # Clear all cache
            result = clear_all_cache()
            cleared_keys = result.get('cleared_keys', 0)
            operation = "Full cache clear"
            
        elif cache_type == "opportunities":
            # Clear only EV/opportunities data
            keys = redis_client.keys('ev_data*')
            if keys:
                redis_client.delete(*keys)
                cleared_keys = len(keys)
            operation = "Opportunities cache clear"
            
        elif cache_type == "analytics":
            # Clear analytics data
            keys = redis_client.keys('analytics*')
            if keys:
                redis_client.delete(*keys)
                cleared_keys = len(keys)
            operation = "Analytics cache clear"
            
        elif cache_type == "sessions":
            # Clear session data (be careful with this!)
            keys = redis_client.keys('session*')
            if keys:
                redis_client.delete(*keys)
                cleared_keys = len(keys)
            operation = "Session cache clear"
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache_type: {cache_type}. Use 'all', 'opportunities', 'analytics', or 'sessions'"
            )
        
        logger.warning(
            f"Cache cleared by admin {admin_user.email}: {operation} - {cleared_keys} keys removed"
        )
        
        return {
            "success": True,
            "message": f"Cache cleared successfully",
            "operation": operation,
            "keys_cleared": cleared_keys,
            "cache_type": cache_type,
            "cleared_by": admin_user.email,
            "timestamp": datetime.now().isoformat(),
            "note": "Data will be refreshed on next request"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/api/celery-health", tags=["system"])
@limiter.limit("30/minute")
async def get_celery_health(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get Celery worker and queue health status
    Admin only endpoint for background task monitoring
    """
    try:
        # Get active workers
        active_workers = celery_app.control.inspect().active()
        stats = celery_app.control.inspect().stats()
        scheduled = celery_app.control.inspect().scheduled()
        
        # Get queue lengths
        try:
            from kombu import Connection
            with Connection(celery_app.conf.broker_url) as conn:
                # This is Redis-specific queue length checking
                queue_lengths = {}
                redis_client = get_redis_client()
                for queue_name in ['celery', 'high_priority', 'low_priority']:
                    try:
                        length = redis_client.llen(queue_name)
                        queue_lengths[queue_name] = length
                    except:
                        queue_lengths[queue_name] = "Unknown"
        except Exception:
            queue_lengths = {"note": "Queue length info unavailable"}
        
        # Calculate worker health
        worker_count = len(active_workers) if active_workers else 0
        healthy_workers = 0
        
        if stats:
            for worker_name, worker_stats in stats.items():
                if worker_stats and 'pool' in worker_stats:
                    healthy_workers += 1
        
        health_status = "healthy" if healthy_workers > 0 else "unhealthy"
        
        return {
            "celery_status": health_status,
            "worker_info": {
                "total_workers": worker_count,
                "healthy_workers": healthy_workers,
                "active_workers": active_workers or {},
                "worker_stats": stats or {}
            },
            "queue_info": {
                "queue_lengths": queue_lengths,
                "scheduled_tasks": len(scheduled) if scheduled else 0
            },
            "broker_info": {
                "broker_url": celery_app.conf.broker_url.split('@')[-1] if '@' in celery_app.conf.broker_url else "Redis",
                "result_backend": "Redis" if "redis" in str(celery_app.conf.result_backend) else "Unknown"
            },
            "checked_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting Celery health: {e}")
        return {
            "celery_status": "error",
            "error": str(e),
            "message": "Failed to retrieve Celery health information",
            "timestamp": datetime.now().isoformat()
        }

@router.post("/api/refresh", tags=["background-tasks"])
@limiter.limit("5/minute")
async def trigger_manual_refresh(
    request: Request,
    background_tasks: BackgroundTasks,
    priority: str = "normal",
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Trigger manual data refresh with priority control
    Admin only endpoint for system maintenance
    """
    try:
        # Validate priority
        valid_priorities = ["low", "normal", "high"]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        
        # Set queue based on priority
        queue_name = {
            "low": "low_priority",
            "normal": "celery",
            "high": "high_priority"
        }.get(priority, "celery")
        
        # Start background refresh task
        task = refresh_odds_data.apply_async(
            queue=queue_name,
            priority={"low": 3, "normal": 6, "high": 9}[priority]
        )
        
        logger.info(
            f"Manual refresh triggered by admin {admin_user.email} with {priority} priority"
        )
        
        return {
            "success": True,
            "message": f"Manual refresh initiated with {priority} priority",
            "task_id": task.id,
            "queue": queue_name,
            "priority": priority,
            "triggered_by": admin_user.email,
            "timestamp": datetime.now().isoformat(),
            "status_check": f"/api/task-status/{task.id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger refresh: {str(e)}"
        )

@router.get("/api/task-status/{task_id}", tags=["background-tasks"])
@limiter.limit("60/minute")
async def get_task_status_endpoint(
    task_id: str,
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get status of a background task by ID
    Admin only endpoint for task monitoring
    """
    try:
        task_info = get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        return {
            "task_id": task_id,
            "status": task_info.get('status', 'UNKNOWN'),
            "result": task_info.get('result'),
            "error": task_info.get('error'),
            "progress": task_info.get('progress', {}),
            "started_at": task_info.get('started_at'),
            "completed_at": task_info.get('completed_at'),
            "duration": task_info.get('duration'),
            "worker": task_info.get('worker'),
            "queue": task_info.get('queue'),
            "checked_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task status: {str(e)}"
        )
"""
Admin Dashboard Routes
Provides administrative functionality for user management and system monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel

# Import authentication dependencies
from core.auth import require_role, UserCtx
from core.session import require_csrf_validation
from core.rate_limit import limiter
from db import get_supabase
from services.redis_cache import get_ev_data, get_last_update

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserRoleUpdate(BaseModel):
    role: str
    reason: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    subscription_status: str
    created_at: Optional[datetime]
    last_sign_in_at: Optional[datetime]
    
class SystemStatsResponse(BaseModel):
    cache_stats: Dict[str, Any]
    database_stats: Dict[str, Any]
    application_stats: Dict[str, Any]
    performance_stats: Dict[str, Any]

@router.get("/users", response_model=Dict[str, Any])
@limiter.limit("30/minute")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    List paginated users with filtering and search capabilities
    Admin only endpoint for user management
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Build Supabase query
        supabase = get_supabase()
        query = supabase.table('profiles').select('id, email, role, subscription_status, created_at')
        
        # Apply filters
        if search:
            query = query.ilike('email', f'%{search}%')
        
        if role:
            query = query.eq('role', role)
        
        # Get total count for pagination
        count_query = supabase.table('profiles').select('id', count='exact')
        if search:
            count_query = count_query.ilike('email', f'%{search}%')
        if role:
            count_query = count_query.eq('role', role)
        
        count_result = count_query.execute()
        total_count = count_result.count
        
        # Execute main query with pagination
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Format response
        users_data = []
        for user in result.data:
            users_data.append({
                "id": str(user.get('id')),
                "email": user.get('email'),
                "role": user.get('role'),
                "subscription_status": user.get('subscription_status'),
                "created_at": user.get('created_at'),
                "last_sign_in_at": None  # Note: auth.users data not directly accessible via REST API
            })
        
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "users": users_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "filters": {
                "search": search,
                "role": role
            },
            "requested_by": admin_user.email
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

@router.post("/users/{user_id}/role")
@limiter.limit("10/minute")
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin")),
    _csrf_valid: bool = Depends(require_csrf_validation)
):
    """
    Update a user's role (admin, subscriber, free)
    Requires admin privileges and CSRF validation
    """
    try:
        # Validate role
        valid_roles = ["admin", "subscriber", "free"]
        if role_update.role not in valid_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Prevent self-demotion from admin
        if admin_user.id == user_id and role_update.role != "admin":
            raise HTTPException(
                status_code=400,
                detail="Cannot change your own admin role"
            )
        
        # Check if user exists using Supabase
        supabase = get_supabase()
        user_result = supabase.table('profiles').select('email, role').eq('id', user_id).execute()
        
        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_result.data[0]
        current_email = user_data.get('email')
        current_role = user_data.get('role')
        
        # Update role in database using Supabase
        update_result = supabase.table('profiles').update({
            'role': role_update.role,
            'updated_at': 'now()'
        }).eq('id', user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update user role")
        
        # Log the role change
        logger.info(
            f"Admin {admin_user.email} changed user {current_email} role from {current_role} to {role_update.role}. "
            f"Reason: {role_update.reason or 'No reason provided'}"
        )
        
        return {
            "success": True,
            "message": f"User role updated to {role_update.role}",
            "user_id": user_id,
            "user_email": current_email,
            "old_role": current_role,
            "new_role": role_update.role,
            "changed_by": admin_user.email,
            "timestamp": datetime.now().isoformat(),
            "reason": role_update.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user role")

@router.get("/stats", response_model=Dict[str, Any])
@limiter.limit("60/minute")
async def get_system_stats(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive system statistics and health metrics
    Admin only endpoint for system monitoring
    """
    try:
        # Cache statistics
        cache_stats = await get_cache_statistics()
        
        # Database statistics
        database_stats = await get_database_statistics(db)
        
        # Application statistics
        app_stats = await get_application_statistics()
        
        # Performance metrics
        performance_stats = await get_performance_statistics()
        
        return {
            "cache_stats": cache_stats,
            "database_stats": database_stats,
            "application_stats": app_stats,
            "performance_stats": performance_stats,
            "generated_at": datetime.now().isoformat(),
            "generated_by": admin_user.email
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

async def get_cache_statistics() -> Dict[str, Any]:
    """Get Redis cache statistics"""
    try:
        import redis
        import os
        
        # Get Redis client directly
        redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        
        # Get basic cache info
        info = redis.info()
        
        # Get EV data info
        ev_data = get_ev_data()
        last_update = get_last_update()
        
        # Check for specific keys
        keys_exist = {}
        important_keys = ['ev_data_all', 'analytics_data', 'last_update_timestamp']
        for key in important_keys:
            keys_exist[key] = redis.exists(key)
        
        return {
            "opportunities_cached": len(ev_data) if ev_data else 0,
            "last_update": last_update,
            "redis_memory_used": info.get('used_memory_human', 'Unknown'),
            "redis_memory_peak": info.get('used_memory_peak_human', 'Unknown'),
            "redis_connected_clients": info.get('connected_clients', 0),
            "redis_total_commands": info.get('total_commands_processed', 0),
            "redis_uptime_days": info.get('uptime_in_days', 0),
            "keys_status": keys_exist,
            "cache_hit_ratio": "Available via Redis INFO"  # Could implement detailed tracking
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": "Cache statistics unavailable"}

async def get_database_statistics(db: AsyncSession) -> Dict[str, Any]:
    """Get database statistics"""
    try:
        # User statistics
        user_stats = await db.execute(text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_users,
                COUNT(CASE WHEN role = 'subscriber' THEN 1 END) as subscriber_users,
                COUNT(CASE WHEN role = 'free' THEN 1 END) as free_users,
                COUNT(CASE WHEN subscription_status = 'active' THEN 1 END) as active_subscriptions,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_users_7d,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_users_30d
            FROM profiles
        """))
        
        user_data = user_stats.fetchone()
        
        return {
            "total_users": user_data[0],
            "users_by_role": {
                "admin": user_data[1],
                "subscriber": user_data[2], 
                "free": user_data[3]
            },
            "active_subscriptions": user_data[4],
            "new_users": {
                "last_7_days": user_data[5],
                "last_30_days": user_data[6]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {"error": "Database statistics unavailable"}

async def get_application_statistics() -> Dict[str, Any]:
    """Get application-level statistics"""
    try:
        from services.tasks import get_celery_stats
        
        # Try to get Celery stats
        try:
            celery_stats = get_celery_stats()
        except Exception:
            celery_stats = {"error": "Celery stats unavailable"}
        
        return {
            "version": "2.1.0",
            "environment": "development",  # Could read from settings
            "celery_stats": celery_stats,
            "active_websockets": 0,  # Could track from ConnectionManager
            "server_uptime": "Available via process monitoring"
        }
        
    except Exception as e:
        logger.error(f"Error getting app stats: {e}")
        return {"error": "Application statistics unavailable"}

async def get_performance_statistics() -> Dict[str, Any]:
    """Get performance-related statistics"""
    try:
        import psutil
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available // 1024 // 1024,
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free // 1024 // 1024 // 1024,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
    except ImportError:
        return {
            "note": "Install psutil for detailed system metrics",
            "cpu_usage_percent": "unavailable",
            "memory_usage_percent": "unavailable"
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {"error": "Performance statistics unavailable"}

@router.delete("/users/{user_id}")
@limiter.limit("5/minute")
async def delete_user(
    user_id: str,
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin")),
    _csrf_valid: bool = Depends(require_csrf_validation),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user account (GDPR/CCPA compliance)
    This is irreversible and should be used carefully
    """
    try:
        # Prevent self-deletion
        if admin_user.id == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own admin account"
            )
        
        # Check if user exists
        user_check = await db.execute(
            text("SELECT email, role FROM profiles WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user_data = user_check.fetchone()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email, user_role = user_data
        
        # Delete from profiles table
        await db.execute(
            text("DELETE FROM profiles WHERE id = :user_id"),
            {"user_id": user_id}
        )
        
        # TODO: Cancel Stripe subscription if exists
        # TODO: Delete from Supabase auth.users if needed
        
        await db.commit()
        
        logger.warning(
            f"Admin {admin_user.email} deleted user account: {user_email} (role: {user_role})"
        )
        
        return {
            "success": True,
            "message": "User account deleted successfully",
            "deleted_user_email": user_email,
            "deleted_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user account") 
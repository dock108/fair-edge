"""
Dashboard Admin Routes
Admin endpoints for monitoring dashboard activity and refresh behavior
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import logging
from datetime import datetime

# Import authentication
from core.auth import require_role, UserCtx
from core.rate_limit import limiter

# Import services
from services.dashboard_activity import dashboard_activity
from services.tasks import refresh_odds_data

# Initialize router
router = APIRouter(tags=["dashboard-admin"])
logger = logging.getLogger(__name__)

@router.get("/api/admin/dashboard/activity")
@limiter.limit("30/minute")
async def get_dashboard_activity_stats(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get comprehensive dashboard activity statistics
    Admin only endpoint for monitoring the smart refresh system
    """
    try:
        logger.info(f"Dashboard activity stats requested by admin: {admin_user.email}")
        
        # Get activity statistics
        activity_stats = dashboard_activity.get_stats()
        
        # Get session information
        sessions_info = dashboard_activity.get_active_sessions_info()
        
        return {
            "dashboard_activity": activity_stats,
            "active_sessions": sessions_info,
            "smart_refresh_config": {
                "session_timeout_seconds": dashboard_activity.session_timeout,
                "refresh_interval_seconds": dashboard_activity.refresh_interval,
                "stale_threshold_seconds": dashboard_activity.stale_threshold,
                "refresh_interval_minutes": dashboard_activity.refresh_interval / 60,
                "stale_threshold_minutes": dashboard_activity.stale_threshold / 60
            },
            "system_status": {
                "last_refresh": activity_stats.get("last_refresh_iso"),
                "time_since_refresh": activity_stats.get("time_since_last_refresh_human"),
                "should_auto_refresh": activity_stats.get("should_auto_refresh"),
                "should_refresh_on_load": activity_stats.get("should_refresh_on_load")
            },
            "timestamp": datetime.now().isoformat(),
            "requested_by": admin_user.email
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard activity stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error retrieving dashboard activity statistics"
        )

@router.post("/api/admin/dashboard/cleanup-sessions")
@limiter.limit("10/minute")
async def cleanup_dashboard_sessions(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Manually cleanup expired dashboard sessions
    Admin only endpoint for maintenance
    """
    try:
        logger.info(f"Manual session cleanup triggered by admin: {admin_user.email}")
        
        # Cleanup expired sessions
        cleaned_count = dashboard_activity.cleanup_expired_sessions()
        
        # Get updated stats
        activity_stats = dashboard_activity.get_stats()
        
        return {
            "success": True,
            "cleaned_sessions": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "current_active_sessions": activity_stats.get("active_sessions", 0),
            "triggered_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up expired sessions"
        )

@router.post("/api/admin/dashboard/test-refresh")
@limiter.limit("5/minute")
async def test_smart_refresh_logic(
    request: Request,
    force_refresh: bool = False,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Test the smart refresh logic
    Admin only endpoint for testing refresh behavior
    """
    try:
        logger.info(f"Smart refresh test triggered by admin: {admin_user.email}")
        
        # Get current activity stats before test
        pre_stats = dashboard_activity.get_stats()
        
        # Test the refresh logic
        should_auto_refresh = dashboard_activity.should_auto_refresh()
        should_refresh_on_load = dashboard_activity.should_refresh_on_load()
        
        # Optionally trigger actual refresh
        task_id = None
        if force_refresh:
            task = refresh_odds_data.delay(force_refresh=True, skip_activity_check=True)
            task_id = task.id
            logger.info(f"Test refresh task started: {task_id}")
        
        return {
            "test_results": {
                "should_auto_refresh": should_auto_refresh,
                "should_refresh_on_load": should_refresh_on_load,
                "has_active_sessions": pre_stats.get("has_active_sessions", False),
                "active_sessions_count": pre_stats.get("active_sessions", 0),
                "time_since_last_refresh_minutes": (pre_stats.get("time_since_last_refresh", 0) / 60) if pre_stats.get("time_since_last_refresh") else None
            },
            "refresh_triggered": force_refresh,
            "task_id": task_id,
            "pre_test_stats": pre_stats,
            "configuration": {
                "refresh_interval_minutes": dashboard_activity.refresh_interval / 60,
                "stale_threshold_minutes": dashboard_activity.stale_threshold / 60,
                "session_timeout_minutes": dashboard_activity.session_timeout / 60
            },
            "triggered_by": admin_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing smart refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error testing smart refresh logic"
        )

@router.get("/api/admin/dashboard/refresh-history")
@limiter.limit("30/minute") 
async def get_refresh_history(
    request: Request,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Get refresh history and timing information
    Admin only endpoint for monitoring refresh patterns
    """
    try:
        logger.info(f"Refresh history requested by admin: {admin_user.email}")
        
        # Get last refresh info
        last_refresh_timestamp = dashboard_activity.get_last_refresh_time()
        
        # Get current activity state
        activity_stats = dashboard_activity.get_stats()
        sessions_info = dashboard_activity.get_active_sessions_info()
        
        history_data = {
            "last_refresh": {
                "timestamp": last_refresh_timestamp,
                "iso_time": datetime.fromtimestamp(last_refresh_timestamp).isoformat() if last_refresh_timestamp else None,
                "time_ago_minutes": (activity_stats.get("time_since_last_refresh", 0) / 60) if activity_stats.get("time_since_last_refresh") else None
            },
            "current_state": {
                "active_sessions": sessions_info["active_sessions_count"],
                "has_active_sessions": sessions_info["has_active_sessions"],
                "should_auto_refresh_now": dashboard_activity.should_auto_refresh(),
                "should_refresh_on_load_now": dashboard_activity.should_refresh_on_load()
            },
            "next_scheduled_actions": {
                "next_auto_refresh_eligible": "15 minutes from last refresh if dashboard is active",
                "refresh_on_load_eligible": "If data is >30 minutes old when dashboard accessed",
                "current_data_age_minutes": (activity_stats.get("time_since_last_refresh", 0) / 60) if activity_stats.get("time_since_last_refresh") else None
            },
            "api_call_optimization": {
                "strategy": "Only refresh when dashboard is active or when stale data accessed",
                "estimated_api_calls_saved": "Approximately 75% reduction compared to fixed 5-minute intervals",
                "current_interval": "15 minutes when active, on-demand when inactive"
            },
            "timestamp": datetime.now().isoformat(),
            "requested_by": admin_user.email
        }
        
        return history_data
        
    except Exception as e:
        logger.error(f"Error getting refresh history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving refresh history"
        )
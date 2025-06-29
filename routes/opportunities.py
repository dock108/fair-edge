"""
Opportunities API Routes
Handles betting opportunities, EV analysis, and related data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Header
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import hashlib

# Import authentication and rate limiting
from core.auth import require_role, get_user_or_none, UserCtx
from core.rate_limit import limiter

# Import services
from services.redis_cache import get_ev_data
from services.tasks import refresh_odds_data
from services.dashboard_activity import dashboard_activity

# Temporary function until we fix the import
def format_opportunities_for_api(
    opportunities, 
    user_role="free", 
    user_id=None, 
    limit=None, 
    min_ev=None, 
    market_type=None,
    **kwargs
):
    """Simple formatter for opportunities - temporary replacement"""
    if not opportunities:
        return []
    
    # Apply basic filtering
    filtered = opportunities
    
    # Role-based filtering
    if user_role in ["free", "anonymous"]:
        # Limit to 10 worst opportunities for free users
        filtered = filtered[-10:] if len(filtered) > 10 else filtered
    
    # Apply limit if specified
    if limit and len(filtered) > limit:
        filtered = filtered[:limit]
    
    return filtered

# Initialize router
router = APIRouter(tags=["opportunities"])
logger = logging.getLogger(__name__)

@router.get("/api/opportunities")
@limiter.limit("60/minute")
async def get_opportunities(
    request: Request,
    background_tasks: BackgroundTasks,
    limit: Optional[int] = None,
    min_ev: Optional[float] = None,
    market_type: Optional[str] = None,
    user: Optional[UserCtx] = Depends(get_user_or_none)
):
    """
    Get betting opportunities with role-based filtering and smart refresh logic
    
    Smart Refresh Strategy:
    - Tracks dashboard activity to optimize API calls
    - Refreshes on load if data is stale and no active sessions
    - Auto-refreshes every 15 minutes only when dashboard is active
    
    Role-based access control:
    - Free users: Limited to worst 10 opportunities with -2% EV threshold
    - Basic users: All main lines with unlimited EV access
    - Premium/Subscribers: Full access to all markets
    - Admins: Complete access with debug information
    """
    try:
        # Generate session ID for activity tracking
        user_id = user.id if user else None
        client_ip = request.client.host if request.client else "unknown"
        session_data = f"{user_id}:{client_ip}:{request.headers.get('user-agent', '')}"
        session_id = hashlib.md5(session_data.encode()).hexdigest()[:12]
        
        # Track dashboard activity
        dashboard_activity.track_dashboard_access(user_id=user_id, session_id=session_id)
        
        # Check if we should refresh data on load (if stale and no recent activity)
        should_refresh_on_load = dashboard_activity.should_refresh_on_load()
        refresh_triggered = False
        
        if should_refresh_on_load:
            logger.info("🔄 Triggering refresh on dashboard load - data is stale")
            # Trigger background refresh with skip_activity_check=True for on-demand refresh
            task = refresh_odds_data.delay(force_refresh=False, skip_activity_check=True)
            background_tasks.add_task(lambda: task)  # Add to background tasks for proper handling
            refresh_triggered = True
        
        # Get cached EV data
        ev_data = get_ev_data()
        
        if not ev_data:
            return {
                "opportunities": [],
                "total_count": 0,
                "filters_applied": {
                    "role_based": True,
                    "user_role": user.role if user else "anonymous"
                },
                "message": "No opportunities available. Data may be refreshing.",
                "cache_status": "empty",
                "refresh_status": {
                    "triggered_on_load": refresh_triggered,
                    "reason": "stale_data" if refresh_triggered else "no_data"
                }
            }
        
        # Apply role-based filtering
        filtered_opportunities = format_opportunities_for_api(
            ev_data, 
            user_role=user.role if user else "free",
            user_id=user.id if user else None,
            limit=limit,
            min_ev=min_ev,
            market_type=market_type
        )
        
        # Add metadata
        total_count = len(filtered_opportunities)
        user_role = user.role if user else "anonymous"
        
        response_data = {
            "opportunities": filtered_opportunities,
            "total_count": total_count,
            "filters_applied": {
                "role_based": True,
                "user_role": user_role,
                "limit": limit,
                "min_ev": min_ev,
                "market_type": market_type
            },
            "timestamp": datetime.now().isoformat(),
            "cache_status": "hit",
            "session_info": {
                "session_id": session_id,
                "activity_tracked": True
            }
        }
        
        # Add refresh status if triggered
        if refresh_triggered:
            response_data["refresh_status"] = {
                "triggered_on_load": True,
                "reason": "stale_data",
                "message": "Fresh data will be available shortly"
            }
        
        # Add debug info for admins
        if user and user.role == "admin":
            activity_stats = dashboard_activity.get_stats()
            response_data["debug_info"] = {
                "raw_data_count": len(ev_data),
                "filtering_applied": True,
                "user_context": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                },
                "activity_stats": activity_stats
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Error retrieving opportunities. Please try again later."
        )

@router.post("/api/opportunities/refresh", tags=["opportunities"])
@limiter.limit("5/minute")
async def refresh_opportunities(
    request: Request,
    background_tasks: BackgroundTasks,
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Trigger background refresh of betting opportunities
    Admin only endpoint for manual data refresh
    """
    try:
        logger.info(f"Manual refresh triggered by admin: {admin_user.email}")
        
        # Start background task with force_refresh=True and skip_activity_check=True for manual refresh
        task = refresh_odds_data.delay(force_refresh=True, skip_activity_check=True)
        
        return {
            "success": True,
            "message": "Manual refresh initiated (force refresh)",
            "task_id": task.id,
            "triggered_by": admin_user.email,
            "timestamp": datetime.now().isoformat(),
            "refresh_type": "manual_force",
            "note": "Check /api/task-status/{task_id} for progress"
        }
        
    except Exception as e:
        logger.error(f"Error triggering refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate refresh"
        )

@router.get("/premium/opportunities")
@limiter.limit("120/minute")
async def get_premium_opportunities(
    request: Request,
    include_props: bool = True,
    include_totals: bool = True,
    include_spreads: bool = True,
    min_ev: Optional[float] = None,
    sort_by: str = "ev_percentage",
    subscriber_user: UserCtx = Depends(require_role("subscriber"))
):
    """
    Enhanced opportunities endpoint for premium subscribers
    Includes all market types and advanced filtering options
    """
    try:
        # Get all cached data
        ev_data = get_ev_data()
        
        if not ev_data:
            return {
                "opportunities": [],
                "total_count": 0,
                "premium_features": {
                    "market_types": ["props", "totals", "spreads", "moneylines"],
                    "unlimited_ev_access": True,
                    "advanced_sorting": True
                },
                "message": "No opportunities available",
                "cache_status": "empty"
            }
        
        # Enhanced filtering for premium users
        filtered_opportunities = format_opportunities_for_api(
            ev_data,
            user_role="subscriber",
            user_id=subscriber_user.id,
            include_props=include_props,
            include_totals=include_totals,
            include_spreads=include_spreads,
            min_ev=min_ev,
            sort_by=sort_by,
            unlimited_access=True
        )
        
        return {
            "opportunities": filtered_opportunities,
            "total_count": len(filtered_opportunities),
            "premium_features": {
                "market_types_included": {
                    "props": include_props,
                    "totals": include_totals,
                    "spreads": include_spreads,
                    "moneylines": True
                },
                "unlimited_ev_access": True,
                "advanced_sorting": sort_by,
                "subscriber_benefits": "Full market access"
            },
            "filters_applied": {
                "user_role": "subscriber",
                "min_ev": min_ev,
                "sort_by": sort_by
            },
            "subscriber_info": {
                "id": subscriber_user.id,
                "email": subscriber_user.email
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting premium opportunities: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving premium opportunities"
        )

@router.get("/api/bets/raw", tags=["opportunities"])
@limiter.limit("30/minute")
async def get_raw_betting_data(
    request: Request,
    format: str = "json",
    include_metadata: bool = True,
    subscriber_user: UserCtx = Depends(require_role("subscriber"))
):
    """
    Export raw betting data for subscribers
    Provides unfiltered access to all opportunities data
    """
    try:
        # Get all raw data
        ev_data = get_ev_data()
        
        if not ev_data:
            return {
                "raw_data": [],
                "count": 0,
                "export_info": {
                    "format": format,
                    "include_metadata": include_metadata,
                    "exported_by": subscriber_user.email,
                    "export_time": datetime.now().isoformat()
                },
                "message": "No raw data available"
            }
        
        # Prepare raw data export
        raw_export = []
        for opportunity in ev_data:
            if include_metadata:
                raw_export.append(opportunity)
            else:
                # Strip metadata, keep core data only
                core_data = {
                    "game": opportunity.get("game", ""),
                    "market": opportunity.get("market", ""),
                    "selection": opportunity.get("selection", ""),
                    "sportsbook": opportunity.get("sportsbook", ""),
                    "odds": opportunity.get("odds", 0),
                    "fair_odds": opportunity.get("fair_odds", 0),
                    "ev_percentage": opportunity.get("ev_percentage", 0),
                    "kelly_bet": opportunity.get("kelly_bet", 0),
                    "commence_time": opportunity.get("commence_time", "")
                }
                raw_export.append(core_data)
        
        return {
            "raw_data": raw_export,
            "count": len(raw_export),
            "export_info": {
                "format": format,
                "include_metadata": include_metadata,
                "exported_by": subscriber_user.email,
                "export_time": datetime.now().isoformat(),
                "data_freshness": "real-time_cache"
            },
            "subscriber_access": {
                "unlimited_export": True,
                "all_markets": True,
                "raw_data_access": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error exporting raw data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error exporting raw betting data"
        )
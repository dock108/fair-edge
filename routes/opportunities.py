"""
Opportunities API Routes
Handles betting opportunities, EV analysis, and related data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Import authentication and rate limiting
from core.auth import require_role, get_user_or_none, UserCtx
from core.rate_limit import limiter

# Import services
from services.redis_cache import get_ev_data, update_ev_data
from services.tasks import refresh_odds_data
from core.ev_analyzer import format_opportunities_for_api

# Initialize router
router = APIRouter(tags=["opportunities"])
logger = logging.getLogger(__name__)

@router.get("/api/opportunities")
@limiter.limit("60/minute")
async def get_opportunities(
    request: Request,
    limit: Optional[int] = None,
    min_ev: Optional[float] = None,
    market_type: Optional[str] = None,
    user: Optional[UserCtx] = Depends(get_user_or_none)
):
    """
    Get betting opportunities with role-based filtering
    
    Role-based access control:
    - Free users: Limited to worst 10 opportunities with -2% EV threshold
    - Basic users: All main lines with unlimited EV access
    - Premium/Subscribers: Full access to all markets
    - Admins: Complete access with debug information
    """
    try:
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
                "cache_status": "empty"
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
            "cache_status": "hit"
        }
        
        # Add debug info for admins
        if user and user.role == "admin":
            response_data["debug_info"] = {
                "raw_data_count": len(ev_data),
                "filtering_applied": True,
                "user_context": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                }
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
        
        # Start background task
        task = refresh_odds_data.delay()
        
        return {
            "success": True,
            "message": "Refresh initiated",
            "task_id": task.id,
            "triggered_by": admin_user.email,
            "timestamp": datetime.now().isoformat(),
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
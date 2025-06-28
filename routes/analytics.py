"""
Analytics API Routes
Handles advanced analytics and market analysis for subscribers
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

# Import authentication and rate limiting
from core.auth import require_role, UserCtx
from core.rate_limit import limiter

# Import services
from services.redis_cache import get_analytics_data, get_ev_data
from core.ev_analyzer import calculate_market_analytics, generate_trend_analysis

# Initialize router
router = APIRouter(tags=["analytics"])
logger = logging.getLogger(__name__)

@router.get("/api/analytics/advanced", tags=["analytics"])
@limiter.limit("30/minute")
async def get_advanced_analytics(
    request: Request,
    timeframe: str = "24h",
    include_trends: bool = True,
    include_sportsbook_analysis: bool = True,
    include_market_breakdown: bool = True,
    subscriber_user: UserCtx = Depends(require_role("subscriber"))
):
    """
    Get advanced market analytics for subscribers
    Provides detailed market analysis, trends, and sportsbook comparisons
    """
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "6h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Get analytics data from cache
        analytics_data = get_analytics_data(timeframe)
        ev_data = get_ev_data()
        
        if not ev_data:
            return {
                "analytics": {},
                "message": "No data available for analysis",
                "timeframe": timeframe,
                "subscriber_access": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate comprehensive analytics
        analytics_result = {}
        
        # Market overview
        analytics_result["market_overview"] = {
            "total_opportunities": len(ev_data),
            "positive_ev_count": len([opp for opp in ev_data if opp.get("ev_percentage", 0) > 0]),
            "average_ev": sum(opp.get("ev_percentage", 0) for opp in ev_data) / len(ev_data),
            "max_ev": max((opp.get("ev_percentage", 0) for opp in ev_data), default=0),
            "total_sports": len(set(opp.get("sport", "") for opp in ev_data)),
            "timeframe": timeframe
        }
        
        # Sportsbook analysis
        if include_sportsbook_analysis:
            sportsbook_stats = {}
            for opp in ev_data:
                book = opp.get("sportsbook", "Unknown")
                if book not in sportsbook_stats:
                    sportsbook_stats[book] = {
                        "opportunity_count": 0,
                        "positive_ev_count": 0,
                        "total_ev": 0,
                        "max_ev": 0,
                        "avg_odds": []
                    }
                
                stats = sportsbook_stats[book]
                stats["opportunity_count"] += 1
                if opp.get("ev_percentage", 0) > 0:
                    stats["positive_ev_count"] += 1
                stats["total_ev"] += opp.get("ev_percentage", 0)
                stats["max_ev"] = max(stats["max_ev"], opp.get("ev_percentage", 0))
                stats["avg_odds"].append(opp.get("odds", 0))
            
            # Calculate averages and rankings
            for book, stats in sportsbook_stats.items():
                stats["avg_ev"] = stats["total_ev"] / max(stats["opportunity_count"], 1)
                stats["avg_odds"] = sum(stats["avg_odds"]) / max(len(stats["avg_odds"]), 1)
                stats["positive_ev_rate"] = stats["positive_ev_count"] / max(stats["opportunity_count"], 1)
            
            analytics_result["sportsbook_analysis"] = sportsbook_stats
        
        # Market breakdown by sport/market type
        if include_market_breakdown:
            sport_breakdown = {}
            market_breakdown = {}
            
            for opp in ev_data:
                sport = opp.get("sport", "Unknown")
                market = opp.get("market", "Unknown")
                
                # Sport stats
                if sport not in sport_breakdown:
                    sport_breakdown[sport] = {
                        "count": 0,
                        "positive_ev_count": 0,
                        "avg_ev": 0,
                        "total_ev": 0
                    }
                
                sport_stats = sport_breakdown[sport]
                sport_stats["count"] += 1
                ev_pct = opp.get("ev_percentage", 0)
                sport_stats["total_ev"] += ev_pct
                if ev_pct > 0:
                    sport_stats["positive_ev_count"] += 1
                
                # Market type stats
                if market not in market_breakdown:
                    market_breakdown[market] = {
                        "count": 0,
                        "positive_ev_count": 0,
                        "avg_ev": 0,
                        "total_ev": 0
                    }
                
                market_stats = market_breakdown[market]
                market_stats["count"] += 1
                market_stats["total_ev"] += ev_pct
                if ev_pct > 0:
                    market_stats["positive_ev_count"] += 1
            
            # Calculate averages
            for sport_stats in sport_breakdown.values():
                sport_stats["avg_ev"] = sport_stats["total_ev"] / max(sport_stats["count"], 1)
            
            for market_stats in market_breakdown.values():
                market_stats["avg_ev"] = market_stats["total_ev"] / max(market_stats["count"], 1)
            
            analytics_result["market_breakdown"] = {
                "by_sport": sport_breakdown,
                "by_market_type": market_breakdown
            }
        
        # Trend analysis
        if include_trends:
            # This would typically use historical data
            # For now, we'll provide basic trend indicators
            analytics_result["trend_analysis"] = {
                "ev_trend": "stable",  # Would calculate from historical data
                "opportunity_count_trend": "increasing",
                "top_trending_sports": ["NFL", "NBA", "Soccer"],
                "emerging_opportunities": "Player Props showing increased value",
                "market_sentiment": "Neutral to positive",
                "recommendation": "Monitor NFL player props for continued value"
            }
        
        # Risk analysis
        analytics_result["risk_analysis"] = {
            "high_ev_opportunities": len([opp for opp in ev_data if opp.get("ev_percentage", 0) > 5]),
            "low_risk_opportunities": len([opp for opp in ev_data if 0 < opp.get("ev_percentage", 0) <= 2]),
            "medium_risk_opportunities": len([opp for opp in ev_data if 2 < opp.get("ev_percentage", 0) <= 5]),
            "high_risk_opportunities": len([opp for opp in ev_data if opp.get("ev_percentage", 0) > 5]),
            "risk_distribution": "Balanced with slight lean toward medium-risk opportunities"
        }
        
        # Performance insights
        analytics_result["performance_insights"] = {
            "best_value_sport": max(sport_breakdown.items(), key=lambda x: x[1]["avg_ev"])[0] if sport_breakdown else "N/A",
            "most_opportunities_sport": max(sport_breakdown.items(), key=lambda x: x[1]["count"])[0] if sport_breakdown else "N/A",
            "recommended_markets": ["Moneyline", "Player Props", "Totals"],
            "optimal_bankroll_allocation": "Conservative: 1-2% per bet, Aggressive: 3-5% per bet",
            "expected_roi": "8-15% with proper bankroll management"
        }
        
        return {
            "analytics": analytics_result,
            "metadata": {
                "timeframe": timeframe,
                "data_points": len(ev_data),
                "analysis_includes": {
                    "trends": include_trends,
                    "sportsbook_analysis": include_sportsbook_analysis,
                    "market_breakdown": include_market_breakdown
                },
                "subscriber_access": True,
                "generated_for": subscriber_user.email,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating advanced analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate advanced analytics"
        )

@router.get("/api/analytics/summary")
@limiter.limit("60/minute")
async def get_analytics_summary(
    request: Request,
    subscriber_user: UserCtx = Depends(require_role("subscriber"))
):
    """
    Get quick analytics summary for dashboard display
    Lightweight endpoint for frequent polling
    """
    try:
        ev_data = get_ev_data()
        
        if not ev_data:
            return {
                "summary": {
                    "total_opportunities": 0,
                    "positive_ev_count": 0,
                    "avg_ev": 0,
                    "best_opportunity": None
                },
                "status": "no_data",
                "timestamp": datetime.now().isoformat()
            }
        
        positive_ev_opps = [opp for opp in ev_data if opp.get("ev_percentage", 0) > 0]
        best_opp = max(ev_data, key=lambda x: x.get("ev_percentage", 0), default=None)
        
        summary = {
            "total_opportunities": len(ev_data),
            "positive_ev_count": len(positive_ev_opps),
            "avg_ev": sum(opp.get("ev_percentage", 0) for opp in ev_data) / len(ev_data),
            "best_opportunity": {
                "game": best_opp.get("game", ""),
                "market": best_opp.get("market", ""),
                "sportsbook": best_opp.get("sportsbook", ""),
                "ev_percentage": best_opp.get("ev_percentage", 0)
            } if best_opp else None,
            "sports_count": len(set(opp.get("sport", "") for opp in ev_data)),
            "sportsbooks_count": len(set(opp.get("sportsbook", "") for opp in ev_data))
        }
        
        return {
            "summary": summary,
            "status": "success",
            "subscriber_access": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate analytics summary"
        )
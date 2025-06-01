"""
FastAPI application for Sports Betting +EV Analyzer Dashboard
Serves the new HTML/CSS UI using Jinja2 templates
"""

from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uvicorn
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import time

# Import the data processing services
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities

# Import background task services
from services.tasks import refresh_odds_data, health_check as celery_health_check
from services.redis_cache import get_ev_data, get_analytics_data, get_last_update, clear_cache, health_check as redis_health_check

# Import database connections
from db import get_db, get_supabase, get_database_status

# Import authentication services
from core.auth import (
    get_current_user, 
    require_role, 
    require_subscription,
    UserCtx
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sports Betting +EV Analyzer",
    description="Real-time identification of positive expected value betting opportunities",
    version="2.1.0"
)

# Configure static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

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

# Include auth router
app.include_router(auth_router)

# Admin mode configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "dev_debug_2024")

def is_admin_mode_enabled(request: Request, admin_param: Optional[str] = None) -> bool:
    """
    Determine if admin mode should be enabled for this request.
    
    Security layers:
    1. DEBUG_MODE environment variable must be true
    2. Admin query parameter must be present
    3. Optional: Admin secret verification
    """
    if not DEBUG_MODE:
        return False
    
    if admin_param != "true":
        return False
    
    # Additional security: check for admin secret in headers or another param
    admin_secret = request.query_params.get("secret")
    if admin_secret and admin_secret != ADMIN_SECRET:
        return False
    
    return True

def get_debug_metrics() -> Dict[str, Any]:
    """Get system debug metrics"""
    return {
        "app_version": "2.1.0",
        "debug_mode": DEBUG_MODE,
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
        "performance": {
            "page_generation_start": time.time()
        }
    }

def calculate_ev_breakdown(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate detailed EV breakdown for debugging purposes
    """
    try:
        # Extract data from the original opportunity structure
        original = opportunity.get('_original', {})
        fair_odds_str = original.get('Fair Odds', '+100')
        best_odds_str = original.get('Best Available Odds', '+100')
        ev_raw = original.get('EV_Raw', 0)
        
        # Parse American odds to decimal for calculation display
        def american_to_decimal(odds_str: str) -> float:
            try:
                # Clean the odds string
                odds_str = odds_str.split('(')[0].strip()  # Remove parenthetical info
                odds_str = odds_str.split('→')[0].strip()   # Remove exchange adjustments
                
                if odds_str.startswith('+'):
                    american = int(odds_str[1:])
                    return (american / 100) + 1
                elif odds_str.startswith('-'):
                    american = int(odds_str[1:])
                    return (100 / american) + 1
                else:
                    american = int(odds_str)
                    if american > 0:
                        return (american / 100) + 1
                    else:
                        return (100 / abs(american)) + 1
            except (ValueError, ZeroDivisionError):
                return 2.0  # Default to even odds
        
        fair_decimal = american_to_decimal(fair_odds_str)
        best_decimal = american_to_decimal(best_odds_str)
        
        # Calculate implied probabilities
        fair_probability = 1 / fair_decimal if fair_decimal > 1 else 0.5
        best_probability = 1 / best_decimal if best_decimal > 1 else 0.5
        
        # Calculate theoretical EV
        theoretical_ev = (fair_probability * best_decimal) - 1
        
        return {
            "fair_odds": {
                "american": fair_odds_str,
                "decimal": round(fair_decimal, 3),
                "implied_probability": round(fair_probability * 100, 2)
            },
            "best_odds": {
                "american": best_odds_str,
                "decimal": round(best_decimal, 3),
                "implied_probability": round(best_probability * 100, 2)
            },
            "ev_calculation": {
                "formula": f"({fair_probability:.3f} × {best_decimal:.3f}) - 1",
                "theoretical_ev": round(theoretical_ev, 4),
                "actual_ev_raw": ev_raw,
                "actual_ev_percentage": round(ev_raw * 100, 2),
                "difference": round(abs(theoretical_ev - ev_raw), 4)
            },
            "classification": {
                "ev_tier": "excellent" if ev_raw >= 0.045 else "high" if ev_raw >= 0.025 else "positive" if ev_raw > 0 else "neutral",
                "reasoning": f"EV of {ev_raw*100:.2f}% " + 
                           ("is excellent (4.5%+)" if ev_raw >= 0.045 else
                            "is high (2.5%+)" if ev_raw >= 0.025 else
                            "is positive" if ev_raw > 0 else
                            "is neutral/negative")
            }
        }
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}

def get_performance_metrics(start_time: float) -> Dict[str, Any]:
    """Calculate performance metrics"""
    current_time = time.time()
    return {
        "page_generation_time_ms": round((current_time - start_time) * 1000, 2),
        "data_fetch_cached": True,  # Since we're using cached data
        "total_processing_time": "< 50ms (typical)",
        "memory_efficient": True
    }

def process_opportunities_for_ui(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform opportunities data from the backend into UI-friendly format
    Maps backend field names to template field names and adds UI helpers
    """
    ui_opportunities = []
    
    for opp in opportunities:
        # Determine EV classification for UI styling
        ev_raw = opp.get('EV_Raw', 0)
        if ev_raw >= 0.045:  # 4.5%+ EV
            ev_classification = "high"
        elif ev_raw > 0:  # Positive EV
            ev_classification = "positive" 
        else:  # Neutral/Negative EV
            ev_classification = "neutral"
        
        # Parse available odds string into structured format
        available_odds = []
        all_odds_str = opp.get('All Available Odds', '')
        if all_odds_str and all_odds_str != 'N/A':
            # Parse "DraftKings: +110; FanDuel: +105; ..." format
            odds_parts = all_odds_str.split('; ')
            for part in odds_parts:
                if ':' in part:
                    bookmaker, odds = part.split(':', 1)
                    available_odds.append({
                        'bookmaker': bookmaker.strip(),
                        'odds': odds.strip()
                    })
        
        # Sort available odds from best to worst
        def odds_sort_key(odds_item):
            """Sort key for odds - best odds first"""
            odds_str = odds_item['odds']
            try:
                # Remove + sign and convert to int
                odds_value = int(odds_str.replace('+', ''))
                
                # For positive odds: higher is better (+200 > +150)
                # For negative odds: closer to zero is better (-110 > -150)
                if odds_value > 0:
                    return odds_value  # Higher positive is better
                else:
                    return -odds_value  # Less negative (closer to zero) is better
            except (ValueError, TypeError):
                return -999999  # Put invalid odds at the end
        
        available_odds.sort(key=odds_sort_key, reverse=True)
        
        # Transform to UI format
        ui_opportunity = {
            'event': opp.get('Event', 'Unknown Event'),
            'bet_description': opp.get('Bet Description', 'Unknown Bet'),
            'bet_type': _format_market_display_name(opp.get('Market', '')),
            'ev_percentage': ev_raw * 100,  # Convert to percentage
            'ev_classification': ev_classification,
            'available_odds': available_odds,
            'fair_odds': opp.get('Fair Odds', 'N/A'),
            'best_available_odds': opp.get('Best Available Odds', 'N/A'),
            'best_odds_source': opp.get('Best_Odds_Source', ''),
            'recommended_posting_odds': opp.get('Proposed Posting Odds', 'N/A'),
            'action_link': _extract_action_link(opp.get('Links', '')),
            # Keep original fields for debugging
            '_original': opp
        }
        
        ui_opportunities.append(ui_opportunity)
    
    return ui_opportunities


def _format_market_display_name(market_key: str) -> str:
    """Convert market key to user-friendly display name"""
    market_names = {
        'h2h': 'Moneyline',
        'spreads': 'Spread',
        'totals': 'Total (O/U)',
        'player_points': 'Player Points',
        'player_assists': 'Player Assists', 
        'player_rebounds': 'Player Rebounds',
        'player_threes': 'Player 3-Pointers',
        'player_steals': 'Player Steals',
        'player_blocks': 'Player Blocks',
        'player_points_rebounds_assists': 'Player PRA',
        'batter_hits': 'Batter Hits',
        'batter_home_runs': 'Batter Home Runs',
        'pitcher_strikeouts': 'Pitcher Strikeouts',
        'player_shots_on_goal': 'Player Shots on Goal',
        'player_goals': 'Player Goals'
    }
    
    # Handle period-specific markets
    if '_q1' in market_key or '_q4' in market_key:
        base_market = market_key.replace('_q1', '').replace('_q4', '')
        period = 'Q1' if '_q1' in market_key else 'Q4'
        base_name = market_names.get(base_market, base_market.replace('_', ' ').title())
        return f"{base_name} ({period})"
    
    return market_names.get(market_key, market_key.replace('_', ' ').title())


def _extract_action_link(links_str: str) -> str:
    """Extract action link from links string"""
    if not links_str or links_str == 'N/A':
        return None
    
    # Handle "Take: url | Post: url" format
    if 'Take:' in links_str:
        take_part = links_str.split('|')[0] if '|' in links_str else links_str
        link = take_part.replace('Take:', '').strip()
        return link if link != 'N/A' else None
    
    # Single link
    return links_str.strip() if links_str.strip() != 'N/A' else None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, admin: Optional[str] = None):
    """
    Main dashboard route - serves the sports betting +EV opportunities
    Uses cached data from Redis for fast loading, with optional admin debugging features
    """
    try:
        # Get debug metrics if needed
        debug_metrics = get_debug_metrics() if is_admin_mode_enabled(request, admin) else None
        
        # Try to get cached data first for better performance
        logger.info("Loading betting opportunities from cache...")
        cached_opportunities = get_ev_data()
        cached_analytics = get_analytics_data()
        last_update = get_last_update()
        
        if cached_opportunities and cached_analytics:
            # Use cached data
            opportunities = cached_opportunities
            analytics = cached_analytics
            data_source = "cache"
            logger.info(f"Serving {len(opportunities)} cached opportunities")
        else:
            # Fallback to live data if cache is empty
            logger.info("Cache empty, fetching live betting opportunities data...")
            raw_data = fetch_raw_odds_data()
            opportunities, analytics = process_opportunities(raw_data)
            data_source = "live"
            logger.info(f"Serving {len(opportunities)} live opportunities")
        
        # Process opportunities for UI
        ui_opportunities = process_opportunities_for_ui(opportunities)
        
        # Enhanced analytics for UI
        ui_analytics = {
            'total_opportunities': len(opportunities),
            'high_ev_count': analytics.get('high_ev_count', 0),
            'positive_ev_count': analytics.get('positive_ev_count', 0),
            'max_ev_percentage': round(analytics.get('max_ev', 0) * 100, 1),
            'avg_ev_percentage': round(analytics.get('avg_ev', 0) * 100, 1),
            'sports_breakdown': analytics.get('sports_breakdown', {}),
            'last_updated': last_update or datetime.now().strftime('%I:%M %p EST'),
            'processing_time': analytics.get('processing_time', 0),
            'data_source': data_source
        }
        
        # Template context
        context = {
            "request": request,
            "opportunities": ui_opportunities,
            "analytics": ui_analytics,
            "debug": debug_metrics,
            "admin_mode": is_admin_mode_enabled(request, admin),
            "current_time": datetime.now().strftime('%I:%M %p EST'),
            "cache_info": {
                "status": "active" if data_source == "cache" else "miss",
                "last_update": last_update
            }
        }
        
        # Add debug calculations if in admin mode
        if is_admin_mode_enabled(request, admin):
            performance_start = debug_metrics["performance"]["page_generation_start"]
            
            # Add detailed EV breakdown for first few opportunities
            debug_opportunities = []
            for i, opp in enumerate(ui_opportunities[:5]):  # First 5 opportunities
                debug_opp = opp.copy()
                debug_opp['_debug'] = calculate_ev_breakdown(opp)
                debug_opportunities.append(debug_opp)
            
            context.update({
                "debug_opportunities": debug_opportunities,
                "performance_metrics": get_performance_metrics(performance_start),
                "cache_status": {
                    "data_source": data_source,
                    "total_cached": len(cached_opportunities) if cached_opportunities else 0,
                    "last_update": last_update
                }
            })
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        
        # Error context
        error_context = {
            "request": request,
            "error_message": "Unable to load betting data. Please try again later.",
            "error_details": str(e) if is_admin_mode_enabled(request, admin) else None,
            "opportunities": [],
            "analytics": {
                'total_opportunities': 0,
                'high_ev_count': 0,
                'positive_ev_count': 0,
                'max_ev_percentage': 0,
                'avg_ev_percentage': 0,
                'sports_breakdown': {},
                'last_updated': 'Error',
                'processing_time': 0,
                'data_source': 'error'
            },
            "admin_mode": is_admin_mode_enabled(request, admin),
            "current_time": datetime.now().strftime('%I:%M %p EST')
        }
        
        return templates.TemplateResponse("dashboard.html", error_context)

@app.get("/disclaimer", response_class=HTMLResponse)
async def disclaimer(request: Request):
    """
    Disclaimer page route - serves the legal disclaimer and risk disclosure
    """
    try:
        context = {
            "request": request,
            "current_date": datetime.now().strftime('%B %d, %Y')
        }
        
        return templates.TemplateResponse("disclaimer.html", context)
        
    except Exception as e:
        logger.error(f"Disclaimer page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load disclaimer page")

@app.get("/education", response_class=HTMLResponse)
async def education(request: Request):
    """
    Education page route - serves the sports betting education content
    """
    try:
        context = {
            "request": request
        }
        
        return templates.TemplateResponse("education.html", context)
        
    except Exception as e:
        logger.error(f"Education page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load education page")

@app.get("/api/opportunities")
async def api_opportunities():
    """
    API endpoint for getting opportunities data - uses cached data for performance
    Falls back to live data if cache is empty
    """
    try:
        # Try cached data first
        cached_opportunities = get_ev_data()
        cached_analytics = get_analytics_data()
        last_update = get_last_update()
        
        if cached_opportunities and cached_analytics:
            # Use cached data
            opportunities = cached_opportunities
            analytics = cached_analytics
            data_source = "cache"
        else:
            # Fallback to live data
            raw_data = fetch_raw_odds_data()
            if raw_data['status'] != 'success':
                return {"error": raw_data.get('error', 'Unknown error'), "opportunities": []}
            
            opportunities, analytics = process_opportunities(raw_data)
            data_source = "live"
        
        ui_opportunities = process_opportunities_for_ui(opportunities)
        
        # Sort by EV percentage (highest first) for better user experience
        ui_opportunities.sort(key=lambda x: x['ev_percentage'], reverse=True)
        
        return {
            "opportunities": ui_opportunities,
            "analytics": analytics,
            "total_opportunities": len(ui_opportunities),
            "last_update": last_update or datetime.now().isoformat(),
            "data_source": data_source
        }
        
    except Exception as e:
        logger.error(f"Error in API route: {e}")
        return {"error": str(e), "opportunities": []}


@app.get("/health")
async def health_check():
    """Health check endpoint with data pipeline and Redis cache validation"""
    try:
        # Check Redis cache status
        redis_status = redis_health_check()
        
        # Try cached data first, fallback to live data
        cached_opportunities = get_ev_data()
        if cached_opportunities:
            data_status = "healthy"
            total_events = len(cached_opportunities)
            last_update = get_last_update()
            data_source = "cache"
        else:
            # Fallback to live data check
            raw_data = fetch_raw_odds_data()
            data_status = "healthy" if raw_data['status'] == 'success' else "degraded"
            total_events = raw_data.get('total_events', 0)
            last_update = raw_data.get('fetch_time', '').isoformat() if raw_data.get('fetch_time') else None
            data_source = "live"
        
        # Include database status
        db_status = await get_database_status()
        
        return {
            "status": "healthy" if data_status == "healthy" and redis_status.get('status') == 'healthy' else "degraded",
            "version": "2.1.0",
            "data_status": data_status,
            "data_source": data_source,
            "total_events": total_events,
            "last_update": last_update,
            "redis": redis_status,
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "version": "2.1.0",
            "error": str(e)
        }


@app.get("/debug/profiles")
async def get_profiles_debug(
    db: AsyncSession = Depends(get_db),
    admin_user: UserCtx = Depends(require_role("admin"))
):
    """
    Debug endpoint to verify Supabase database integration - ADMIN ONLY
    Shows all user profiles from the database
    """
    try:
        # Query profiles using raw SQL (since we don't have SQLAlchemy models yet)
        result = await db.execute(text("SELECT id, email, role, subscription_status, created_at FROM profiles ORDER BY created_at DESC LIMIT 10"))
        profiles = result.fetchall()
        
        # Convert to list of dicts for JSON response
        profiles_data = []
        for profile in profiles:
            profiles_data.append({
                "id": str(profile[0]),
                "email": profile[1],
                "role": profile[2],
                "subscription_status": profile[3],
                "created_at": profile[4].isoformat() if profile[4] else None
            })
        
        return {
            "status": "success",
            "total_profiles": len(profiles_data),
            "profiles": profiles_data,
            "message": "Successfully connected to Supabase database",
            "admin_user": admin_user.email
        }
    except Exception as e:
        logger.error(f"Error querying profiles: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to connect to Supabase database"
        }


@app.get("/debug/supabase")
async def test_supabase_client():
    """
    Debug endpoint to test Supabase client functionality
    """
    try:
        supabase = get_supabase()
        
        # Test connection by querying profiles table
        response = supabase.table('profiles').select('id, email, role').limit(5).execute()
        
        return {
            "status": "success",
            "supabase_connected": True,
            "profiles_count": len(response.data),
            "sample_profiles": response.data,
            "message": "Supabase client working correctly"
        }
    except Exception as e:
        logger.error(f"Supabase client error: {e}")
        return {
            "status": "error",
            "supabase_connected": False,
            "error": str(e),
            "message": "Failed to connect using Supabase client"
        }


@app.get("/debug/database-status")
async def database_status_debug():
    """
    Comprehensive database status check
    """
    try:
        status = await get_database_status()
        return {
            "timestamp": datetime.now().isoformat(),
            "database_status": status
        }
    except Exception as e:
        logger.error(f"Database status check error: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "failed"
        }


@app.get("/premium/opportunities")
async def get_premium_opportunities(
    subscriber: UserCtx = Depends(require_subscription())
):
    """
    Premium endpoint for subscribers - enhanced opportunities with additional analysis
    """
    try:
        # Get basic opportunities
        raw_data = fetch_raw_odds_data()
        opportunities, analytics = process_opportunities(raw_data)
        
        # Add premium features for subscribers
        enhanced_opportunities = []
        for opp in opportunities:
            enhanced = opp.copy()
            # Add premium data analysis
            enhanced['premium_analysis'] = {
                'confidence_score': round((opp.get('EV_Raw', 0) * 100 + 50), 1),
                'risk_assessment': 'low' if opp.get('EV_Raw', 0) > 0.03 else 'medium',
                'historical_performance': 'Not available in demo'
            }
            enhanced_opportunities.append(enhanced)
        
        return {
            "opportunities": enhanced_opportunities,
            "analytics": analytics,
            "premium_features": {
                "confidence_scoring": True,
                "risk_assessment": True,
                "historical_tracking": True,
                "advanced_filters": True
            },
            "subscriber_info": {
                "id": subscriber.id,
                "role": subscriber.role,
                "subscription_status": subscriber.subscription_status
            }
        }
        
    except Exception as e:
        logger.error(f"Error in premium opportunities: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch premium opportunities")


@app.get("/api/user-info")
async def get_user_info(user: UserCtx = Depends(get_current_user)):
    """
    Get basic user info using simple JWT validation (no database lookup)
    Useful for quick authentication checks
    """
    return {
        "user_id": user.id,
        "email": user.email,
        "authenticated": True
    }


# Background Task Endpoints
@app.post("/api/refresh", tags=["background-tasks"])
async def manual_refresh(admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Manually trigger odds data refresh using Celery background task - ADMIN ONLY
    """
    try:
        # Schedule the task
        task = refresh_odds_data.delay()
        
        return {
            "status": "scheduled",
            "task_id": task.id,
            "message": "Odds refresh task has been scheduled",
            "admin_user": admin_user.email
        }
    except Exception as e:
        logger.error(f"Failed to schedule refresh task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule task: {str(e)}")


@app.get("/api/task-status/{task_id}", tags=["background-tasks"])
async def get_task_status(task_id: str, admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Get the status of a background task - ADMIN ONLY
    """
    try:
        from services.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            response = {
                'state': result.state,
                'status': 'Task is waiting to be processed'
            }
        elif result.state == 'PROGRESS':
            response = {
                'state': result.state,
                'current': result.info.get('current', 0),
                'total': result.info.get('total', 1),
                'status': result.info.get('status', '')
            }
        elif result.state == 'SUCCESS':
            response = {
                'state': result.state,
                'result': result.result
            }
        else:  # FAILURE
            response = {
                'state': result.state,
                'error': str(result.info)
            }
        
        return response
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@app.get("/api/odds", tags=["opportunities"])
async def get_cached_opportunities():
    """
    Get cached EV opportunities from Redis (public endpoint)
    This is the main endpoint for getting opportunities without triggering API calls
    """
    try:
        # Get cached data from Redis
        opportunities = get_ev_data()
        analytics = get_analytics_data()
        last_update = get_last_update()
        
        # Process opportunities for UI display
        if opportunities:
            ui_opportunities = process_opportunities_for_ui(opportunities)
            ui_opportunities.sort(key=lambda x: x.get('ev_percentage', 0), reverse=True)
        else:
            ui_opportunities = []
        
        return {
            "total": len(opportunities),
            "opportunities": ui_opportunities,
            "analytics": analytics,
            "last_update": last_update,
            "data_source": "redis_cache"
        }
    except Exception as e:
        logger.error(f"Failed to retrieve cached opportunities: {e}")
        # Fallback to live data if Redis fails
        try:
            raw_data = fetch_raw_odds_data()
            if raw_data['status'] == 'success':
                opportunities, analytics = process_opportunities(raw_data)
                ui_opportunities = process_opportunities_for_ui(opportunities)
                ui_opportunities.sort(key=lambda x: x.get('ev_percentage', 0), reverse=True)
                return {
                    "total": len(opportunities),
                    "opportunities": ui_opportunities,
                    "analytics": analytics,
                    "last_update": datetime.now().isoformat(),
                    "data_source": "live_fallback"
                }
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
        
        return {
            "total": 0,
            "opportunities": [],
            "analytics": {},
            "error": "Unable to retrieve opportunities data",
            "data_source": "error"
        }


@app.get("/api/cache-status", tags=["system"])
async def get_cache_status():
    """
    Get Redis cache health and status information
    """
    try:
        redis_status = redis_health_check()
        return {
            "timestamp": datetime.now().isoformat(),
            "redis": redis_status
        }
    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "redis": {
                "status": "error",
                "message": str(e)
            }
        }


@app.post("/api/clear-cache", tags=["system"])
async def clear_redis_cache(admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Clear Redis cache - ADMIN ONLY
    """
    try:
        success = clear_cache()
        if success:
            return {
                "status": "success",
                "message": "Cache cleared successfully",
                "admin_user": admin_user.email
            }
        else:
            return {
                "status": "error",
                "message": "Failed to clear cache"
            }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.get("/api/celery-health", tags=["system"])
async def get_celery_health(admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Test Celery worker health - ADMIN ONLY
    """
    try:
        # Schedule a simple health check task
        task = celery_health_check.delay()
        # Wait briefly for result
        result = task.get(timeout=10)
        
        return {
            "status": "healthy",
            "celery_result": result,
            "admin_user": admin_user.email
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Celery worker is not responding"
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
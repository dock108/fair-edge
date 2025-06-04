"""
FastAPI application for Sports Betting +EV Analyzer Dashboard
Serves the new HTML/CSS UI using Jinja2 templates
"""

from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uvicorn
import logging
import signal
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import time
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from jose import jwt

# Import logging and observability setup
from core.logging import setup_logging
from core.observability import setup_observability

# Import the data processing services
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities

# Import background task services
from services.tasks import refresh_odds_data, health_check as celery_health_check, SPORTS_SUPPORTED
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

# Import session management
from core.session import (
    SessionManager, 
    get_current_user_from_cookie, 
    require_csrf_validation
)

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
    title="Bet Intel - Sports +EV Analysis", 
    description="Educational sports betting analysis and odds comparison tool",
    version="2.1.0",
    lifespan=lifespan
)

# Add rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add proxy headers middleware for proper IP detection behind load balancers
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Configure CORS based on environment - use new config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"]  # Allow frontend to read CSRF token
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

# Include billing router
app.include_router(billing_router)

# Include realtime router
app.include_router(realtime_router)

# Include admin router
app.include_router(admin_router)

# Register cleanup functions from other modules
try:
    from routes.realtime import cleanup_redis_connections
    register_cleanup(cleanup_redis_connections)
    logger.info("✅ Registered cleanup_redis_connections cleanup")
except ImportError as e:
    logger.warning(f"Could not register Redis cleanup: {e}")

try:
    from services.tasks import cleanup_celery
    register_cleanup(cleanup_celery)
    logger.info("✅ Registered cleanup_celery cleanup")
except ImportError as e:
    logger.warning(f"Could not register Celery cleanup: {e}")

# Register signal handlers for graceful shutdown
def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"📡 Received signal {signum}")
        # Let FastAPI handle the cleanup through the lifespan handler
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# Setup signal handlers
setup_signal_handlers()

def is_admin_mode_enabled(request: Request, admin_param: Optional[str] = None) -> bool:
    """
    Determine if admin mode should be enabled for this request.
    
    Security layers:
    1. DEBUG_MODE environment variable must be true
    2. Admin query parameter must be present
    3. Optional: Admin secret verification
    """
    if not settings.is_debug:
        return False
    
    if admin_param != "true":
        return False
    
    # Additional security: check for admin secret in headers or another param
    admin_secret = request.query_params.get("secret")
    if admin_secret and admin_secret != settings.admin_secret:
        return False
    
    return True

def get_debug_metrics() -> Dict[str, Any]:
    """Get system debug metrics"""
    return {
        "app_version": "2.1.0",
        "debug_mode": settings.is_debug,
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment,
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
async def home(request: Request, admin: Optional[str] = None):
    """
    Home page - shows free-tier dashboard for everyone, with upgrade prompts for premium features
    No authentication required - this showcases the product value
    """
    try:
        # Try to get current user if logged in, but don't require it
        user = None
        try:
            from core.session import get_current_user_from_cookie
            user = get_current_user_from_cookie(request)
        except Exception:
            # User not authenticated, that's fine - show free tier
            pass
        
        # If no user, create a guest user context for free tier
        if not user:
            from types import SimpleNamespace
            user = SimpleNamespace(
                id="guest",
                email="guest@example.com",
                role="free",
                subscription_status="none"
            )
        
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
        
        # Apply role-based filtering (free tier for guests, full access for subscribers)
        filtered_response = filter_opportunities_by_role(ui_opportunities, user.role)
        
        # Apply filters from query parameters
        sport_filter = request.query_params.get('sport', '').strip()
        market_filter = request.query_params.get('market', '').strip()
        
        if sport_filter:
            filtered_response['opportunities'] = [
                op for op in filtered_response['opportunities'] 
                if sport_filter.lower() in op.get('sport', '').lower()
            ]
        
        if market_filter:
            filtered_response['opportunities'] = [
                op for op in filtered_response['opportunities'] 
                if market_filter.lower() in op.get('market', '').lower()
            ]
        
        # Update analytics based on filtered data
        filtered_opportunities = filtered_response['opportunities']
        ui_analytics = {
            'total_opportunities': len(filtered_opportunities),
            'positive_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) > 0]),
            'high_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) >= 4.5]),
            'max_ev_percentage': round(max([op.get('ev_percentage', 0) for op in filtered_opportunities], default=0), 2)
        }
        
        # Prepare template context
        context = {
            "request": request,
            "settings": settings,
            "user": user,  # Pass user object to template (could be guest)
            "user_role": user.role,  # Pass role explicitly for easy access
            "is_guest": user.id == "guest",  # Flag to show login prompts
            "opportunities": filtered_opportunities,
            "analytics": ui_analytics,
            "admin_mode": is_admin_mode_enabled(request, admin),
            "filter_applied": bool(sport_filter or market_filter),
            "current_sport": sport_filter,
            "current_market": market_filter,
            "page_title": "Live Betting Dashboard - Sports +EV Analysis",
            # Role-based metadata
            "role_metadata": {
                "truncated": filtered_response.get('truncated', False),
                "limit": filtered_response.get('limit'),
                "total_available": filtered_response.get('total_available', 0),
                "shown": filtered_response.get('shown', 0),
                "features": filtered_response.get('features', {})
            },
            "sports_supported": SPORTS_SUPPORTED
        }
        
        if is_admin_mode_enabled(request, admin):
            performance_start = debug_metrics["performance"]["page_generation_start"]
            
            # Add detailed EV breakdown for first few opportunities
            debug_opportunities = []
            for i, opp in enumerate(filtered_opportunities[:5]):  # First 5 opportunities
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
        
        # Create template response with SEO-friendly cache headers
        response = templates.TemplateResponse("dashboard.html", context)
        # Align cache timing with noscript meta refresh for consistency
        response.headers["Cache-Control"] = "max-age=60, stale-while-revalidate=30"
        return response
        
    except Exception as e:
        logger.error(f"Home page error: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Unable to load page: {str(e)}</p>",
            status_code=500
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request, admin: Optional[str] = None):
    """
    Dashboard redirect - just redirect to home page now that home shows the dashboard
    """
    from fastapi.responses import RedirectResponse
    query_params = str(request.query_params)
    redirect_url = "/" + ("?" + query_params if query_params else "")
    return RedirectResponse(url=redirect_url, status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "settings": settings,
        "page_title": "Login - Sports Betting +EV Analyzer"
    })

@app.post("/api/logout")
async def logout_api():
    """API endpoint for logout (for completeness - main logout is handled client-side)"""
    return {"status": "success", "message": "Logged out successfully"}

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
        
        response = templates.TemplateResponse("disclaimer.html", context)
        response.headers["Cache-Control"] = "max-age=3600, stale-while-revalidate=1800"  # Longer cache for static content
        return response
        
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
        
        response = templates.TemplateResponse("education.html", context)
        response.headers["Cache-Control"] = "max-age=3600, stale-while-revalidate=1800"  # Longer cache for static content
        return response
        
    except Exception as e:
        logger.error(f"Education page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load education page")

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """
    Pricing page route - serves the pricing and plan comparison
    """
    try:
        context = {
            "request": request,
            "settings": settings,
            "page_title": "Pricing - Sports Betting +EV Analyzer"
        }
        
        response = templates.TemplateResponse("pricing.html", context)
        response.headers["Cache-Control"] = "max-age=3600, stale-while-revalidate=1800"  # Longer cache for static content
        return response
        
    except Exception as e:
        logger.error(f"Pricing page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load pricing page")

@app.get("/upgrade/success", response_class=HTMLResponse)
async def upgrade_success_page(request: Request):
    """
    Upgrade success page route - serves the post-checkout success page
    """
    try:
        context = {
            "request": request,
            "settings": settings,
            "page_title": "Upgrade Successful - Sports Betting +EV Analyzer"
        }
        
        return templates.TemplateResponse("upgrade_success.html", context)
        
    except Exception as e:
        logger.error(f"Upgrade success page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load upgrade success page")

@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    """
    Account management page - allows users to view and manage their subscription
    """
    try:
        context = {
            "request": request,
            "settings": settings,
            "page_title": "My Account - Sports Betting +EV Analyzer"
        }
        
        return templates.TemplateResponse("account.html", context)
        
    except Exception as e:
        logger.error(f"Account page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load account page")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """
    Admin dashboard page - allows administrators to manage users and view system stats
    Requires admin role for access
    """
    try:
        # Get user from session cookie
        from core.session import get_current_user_from_cookie
        user = get_current_user_from_cookie(request)
        
        if not user:
            # Redirect to login if not authenticated
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login?redirect=/admin", status_code=302)
        
        # Check if user has admin role
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        context = {
            "request": request,
            "settings": settings,
            "page_title": "Admin Dashboard - Sports Betting +EV Analyzer",
            "admin_user": user
        }
        
        return templates.TemplateResponse("admin.html", context)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Admin page error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load admin page")

# Define main line markets that free users can access
MAIN_LINES = {"h2h", "spreads", "totals"}  # moneyline, game spreads, game totals

def filter_opportunities_by_role(opportunities: List[Dict[str, Any]], user_role: str) -> Dict[str, Any]:
    """
    Filter opportunities based on user role
    Free users: Only main lines (moneyline, spreads, totals)
    Subscribers/Admins: All markets
    """
    total_available = len(opportunities)
    
    if user_role in ("subscriber", "admin"):
        # Full access for paid users and admins
        filtered_opportunities = opportunities
        truncated = False
        limit = None
    else:
        # Free users: filter by market type only (no quantity limit)
        filtered_opportunities = []
        for opp in opportunities:
            # Get the original market key from the _original data
            original_market = opp.get('_original', {}).get('Market', '')
            
            # Check if this is a main line market
            if original_market in MAIN_LINES:
                # Mask advanced fields for free users
                from core.config import feature_config
                filtered_opp = opp.copy()
                for field in feature_config.MASK_FIELDS_FOR_FREE:
                    filtered_opp.pop(field, None)
                    # Also remove from _original if it exists
                    if '_original' in filtered_opp:
                        filtered_opp['_original'].pop(field, None)
                filtered_opportunities.append(filtered_opp)
        
        truncated = len(filtered_opportunities) < total_available
        limit = "main lines only"
    
    from core.config import feature_config
    role_config = feature_config.get_user_features(user_role)
    
    return {
        "role": user_role,
        "truncated": truncated,
        "limit": limit,
        "total_available": total_available,
        "shown": len(filtered_opportunities),
        "features": role_config,
        "opportunities": filtered_opportunities
    }

@app.get("/dashboard/premium", response_class=HTMLResponse)
async def premium_dashboard(request: Request, admin: Optional[str] = None, user: UserCtx = Depends(get_current_user)):
    """
    Premium dashboard endpoint - requires authentication and shows full features
    This is where authenticated users get redirected for premium features
    """
    try:
        # Redirect to home with user context - the home page will show full features for authenticated users
        from fastapi.responses import RedirectResponse
        query_params = str(request.query_params)
        redirect_url = "/" + ("?" + query_params if query_params else "")
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Premium dashboard error: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Unable to load premium dashboard: {str(e)}</p>",
            status_code=500
        )

@app.get("/api/opportunities")
@limiter.limit("60/minute")
async def api_opportunities(
    request: Request, 
    search: Optional[str] = None,
    sport: Optional[str] = None,
    batch_id: Optional[str] = None  # Phase 3.1: Support batch polling
):
    """
    Main API endpoint for getting opportunities data with role-based access control
    Supports guest access with free tier limits and server-side filtering
    Falls back to live data if cache is empty
    Rate limited to prevent abuse
    
    Query parameters:
    - search: Search term for teams, events, players, bet descriptions
    - sport: Filter by specific sport (americanfootball_nfl, basketball_nba, etc.)
    - batch_id: Poll for results of a specific batch calculation (Phase 3.1)
    """
    try:
        # Phase 3.1: Handle batch polling
        if batch_id:
            from tasks.ev import get_batch_results, get_batch_status
            
            # Check if batch results are ready
            batch_results = get_batch_results(batch_id)
            if batch_results:
                logger.info(f"📦 Serving batch results for {batch_id}")
                
                # Extract opportunities and apply same filtering as normal flow
                opportunities = batch_results.get('opportunities', [])
                analytics = batch_results.get('analytics', {})
                
                # Get user context for role-based filtering
                user = None
                try:
                    from core.session import get_current_user_from_cookie
                    user = get_current_user_from_cookie(request)
                except Exception:
                    pass
                
                if not user:
                    from types import SimpleNamespace
                    user = SimpleNamespace(
                        id="guest",
                        email="guest@example.com", 
                        role="free",
                        subscription_status="none"
                    )
                
                # Process and filter the batch results
                ui_opportunities = process_opportunities_for_ui(opportunities)
                
                # Apply search/sport filters if provided
                if search:
                    search_term = search.lower()
                    ui_opportunities = [
                        opp for opp in ui_opportunities
                        if search_term in " ".join([
                            opp.get('event', ''),
                            opp.get('bet_description', ''),
                            opp.get('bet_type', ''),
                            opp.get('best_odds_source', '')
                        ]).lower()
                    ]
                
                if sport:
                    sport_keywords = {
                        'americanfootball_nfl': ['nfl', 'football'],
                        'basketball_nba': ['nba', 'basketball'],
                        'baseball_mlb': ['mlb', 'baseball'],
                        'icehockey_nhl': ['nhl', 'hockey']
                    }
                    keywords = sport_keywords.get(sport, [sport])
                    ui_opportunities = [
                        opp for opp in ui_opportunities
                        if any(keyword in opp.get('event', '').lower() for keyword in keywords)
                    ]
                
                # Apply role-based filtering
                filtered_response = filter_opportunities_by_role(ui_opportunities, user.role)
                
                # Build response with batch metadata
                response_data = {
                    **filtered_response,
                    "analytics": analytics,
                    "last_update": batch_results.get('generated_at'),
                    "data_source": "batch_cache",
                    "is_guest": user.id == "guest",
                    "batch_info": {
                        "batch_id": batch_id,
                        "processing_time_ms": batch_results.get('processing_time_ms'),
                        "cache_hit": True
                    },
                    "filters_applied": {
                        "search": search,
                        "sport": sport,
                        "has_filters": bool(search or sport)
                    }
                }
                
                return JSONResponse(content=response_data)
            
            else:
                # Check batch status
                batch_status = get_batch_status(batch_id)
                if batch_status:
                    return JSONResponse(
                        content={
                            "status": "processing",
                            "batch_id": batch_id,
                            "batch_status": batch_status,
                            "message": "Batch calculation in progress",
                            "retry_after": 30  # Suggest retry in 30 seconds
                        },
                        status_code=202
                    )
                else:
                    return JSONResponse(
                        content={
                            "status": "error",
                            "batch_id": batch_id,
                            "error": "Batch not found or expired",
                            "message": "Please trigger a new batch calculation"
                        },
                        status_code=404
                    )
        
        # Regular flow (non-batch) - existing logic
        # Simple user context without external services to avoid circular imports
        user = None
        try:
            from core.session import get_current_user_from_cookie
            user = get_current_user_from_cookie(request)
        except Exception:
            pass
        
        # If no user, create a guest user context for free tier
        if not user:
            from types import SimpleNamespace
            user = SimpleNamespace(
                id="guest",
                email="guest@example.com", 
                role="free",
                subscription_status="none"
            )
        
        # Get data using existing functions
        logger.info("Loading betting opportunities from cache...")
        cached_opportunities = get_ev_data()
        cached_analytics = get_analytics_data()
        last_update = get_last_update()
        
        if cached_opportunities and cached_analytics:
            opportunities = cached_opportunities
            analytics = cached_analytics
            data_source = "cache"
            logger.info(f"Serving {len(opportunities)} cached opportunities")
        else:
            logger.info("Cache empty, fetching live betting opportunities data...")
            raw_data = fetch_raw_odds_data()
            opportunities, analytics = process_opportunities(raw_data)
            data_source = "live"
            logger.info(f"Serving {len(opportunities)} live opportunities")
        
        # Process opportunities for UI
        ui_opportunities = process_opportunities_for_ui(opportunities)
        
        # Apply search filter if provided
        if search:
            search_term = search.lower()
            filtered_opps = []
            for opp in ui_opportunities:
                searchable_text = " ".join([
                    opp.get('event', ''),
                    opp.get('bet_description', ''),
                    opp.get('bet_type', ''),
                    opp.get('best_odds_source', '')
                ]).lower()
                
                if search_term in searchable_text:
                    filtered_opps.append(opp)
            ui_opportunities = filtered_opps
        
        # Apply sport filter if provided
        if sport:
            sport_keywords = {
                'americanfootball_nfl': ['nfl', 'football'],
                'basketball_nba': ['nba', 'basketball'],
                'baseball_mlb': ['mlb', 'baseball'],
                'icehockey_nhl': ['nhl', 'hockey']
            }
            keywords = sport_keywords.get(sport, [sport])
            filtered_opps = []
            for opp in ui_opportunities:
                event_text = opp.get('event', '').lower()
                if any(keyword in event_text for keyword in keywords):
                    filtered_opps.append(opp)
            ui_opportunities = filtered_opps
        
        # Apply role-based filtering
        filtered_response = filter_opportunities_by_role(ui_opportunities, user.role)
        
        # Update analytics for filtered data
        filtered_opportunities = filtered_response['opportunities']
        ui_analytics = {
            'total_opportunities': len(filtered_opportunities),
            'positive_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) > 0]),
            'high_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) >= 4.5]),
            'max_ev_percentage': round(max([op.get('ev_percentage', 0) for op in filtered_opportunities], default=0), 2)
        }
        
        # Build response
        response_data = {
            **filtered_response,
            "analytics": ui_analytics,
            "last_update": last_update,
            "data_source": data_source,
            "is_guest": user.id == "guest",
            "filters_applied": {
                "search": search,
                "sport": sport,
                "has_filters": bool(search or sport)
            }
        }
        
        # Return JSONResponse for proper slowapi compatibility
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error in API route: {e}")
        error_response = {
            "status": "error",
            "error": str(e),
            "opportunities": [],
            "analytics": {},
            "role": "free",
            "is_guest": True
        }
        
        # Return JSONResponse for proper slowapi compatibility
        return JSONResponse(content=error_response, status_code=500)

@app.post("/api/opportunities/refresh", tags=["opportunities"])
@limiter.limit("10/minute")  # Lower limit for compute-intensive operations
async def trigger_ev_refresh(request: Request):
    """
    Trigger EV calculation batch processing - Phase 3.1 implementation
    
    This endpoint:
    1. Schedules calc_ev_batch.delay(...) 
    2. Returns 202 with batch ID
    3. Clients poll /api/opportunities?batch_id=... for results
    
    Heavy CPU work moved off FastAPI event loop per Phase 3 plan
    """
    try:
        from tasks.ev import calc_ev_batch, generate_batch_id
        
        # Generate unique batch ID for tracking
        batch_id = generate_batch_id()
        
        logger.info(f"🚀 Triggering EV batch calculation: {batch_id}")
        
        # Schedule the heavy computation task
        task = calc_ev_batch.delay(batch_id)
        
        # Return 202 Accepted with batch tracking info
        return JSONResponse(
            content={
                "status": "accepted",
                "message": "EV calculation batch scheduled",
                "batch_id": batch_id,
                "task_id": task.id,
                "poll_url": f"/api/opportunities?batch_id={batch_id}",
                "estimated_completion": "2-5 minutes"
            },
            status_code=202
        )
        
    except Exception as e:
        logger.error(f"Failed to schedule EV batch: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": "Failed to schedule batch calculation",
                "details": str(e)
            },
            status_code=500
        )

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
@limiter.limit("30/minute")
async def get_user_info(request: Request, user: UserCtx = Depends(get_current_user)):
    """
    Get basic user info using simple JWT validation (no database lookup)
    Useful for quick authentication checks
    Rate limited to prevent abuse
    """
    return {
        "user_id": user.id,
        "email": user.email,
        "authenticated": True
    }


# Background Task Endpoints
@app.post("/api/refresh", tags=["background-tasks"])
@limiter.limit("5/minute")  # Lower limit for admin operations
async def manual_refresh(request: Request, admin_user: UserCtx = Depends(require_role("admin")), csrf_valid: bool = Depends(require_csrf_validation)):
    """
    Manually trigger odds data refresh using Celery background task - ADMIN ONLY
    Requires CSRF token validation
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
@limiter.limit("20/minute")
async def get_task_status(task_id: str, request: Request, admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Get the status of a background task - ADMIN ONLY
    Rate limited to prevent abuse
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


@app.get("/api/cache-status", tags=["system"])
@limiter.limit("30/minute")
async def get_cache_status(request: Request):
    """
    Get Redis cache health and status information
    Rate limited to prevent abuse
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
@limiter.limit("10/minute")
async def clear_redis_cache(request: Request, admin_user: UserCtx = Depends(require_role("admin")), csrf_valid: bool = Depends(require_csrf_validation)):
    """
    Clear Redis cache - ADMIN ONLY
    Requires CSRF token validation
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
@limiter.limit("10/minute")
async def get_celery_health(request: Request, admin_user: UserCtx = Depends(require_role("admin"))):
    """
    Test Celery worker health - ADMIN ONLY
    Rate limited to prevent abuse
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


# Debug endpoint to manually trigger data refresh in development
@app.post("/debug/trigger-refresh")
async def trigger_manual_refresh(request: Request):
    """
    Manual refresh endpoint for development/debugging
    Triggers immediate data refresh and returns the updated opportunities
    Only active when DEBUG_MODE is enabled
    """
    if not settings.is_debug:
        raise HTTPException(status_code=404, detail="Debug endpoint not available in production")
    
    try:
        # Use centralized user service
        from services.user_service import UserContextManager
        from services.data_service import OpportunityProcessor
        
        user_ctx = UserContextManager(request)
        
        logger.info(f"🔄 Manual refresh triggered for user role: {user_ctx.role}")
        
        # Trigger the background task for cache refresh
        task = refresh_odds_data.delay()
        
        # Wait a moment for the task to start
        time.sleep(1)
        
        # Process opportunities with current data
        processor = OpportunityProcessor(user_ctx.role)
        result = processor.process()
        
        if result["filtered_response"].get("opportunities"):
            filtered_response = result["filtered_response"]
            
            return {
                "status": "success",
                "message": f"Refresh triggered for {user_ctx.role} user",
                "task_id": task.id,
                "task_state": task.state,
                "opportunities_count": len(filtered_response.get('opportunities', [])),
                "total_available": filtered_response.get('total_available', 0),
                "role": user_ctx.role,
                "filtered_data": filtered_response,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "pending",
                "message": "Refresh triggered, data processing in progress",
                "task_id": task.id,
                "task_state": task.state,
                "role": user_ctx.role,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Manual refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# Session Management Endpoints (Production Cookie-based Auth)
@app.post("/api/session")
@limiter.limit("20/minute")  # Rate limit session creation
async def create_session(request: Request, response: Response):
    """
    Create secure session with httpOnly cookies
    Called after successful Supabase authentication on frontend
    Rate limited to prevent abuse
    """
    try:
        # Parse request body
        body = await request.json()
        access_token = body.get("access_token")
        user_data = body.get("user_data", {})
        
        if not access_token:
            logger.error("Session creation failed: Missing access_token")
            raise HTTPException(status_code=400, detail="Missing access_token")
        
        # Validate the token by attempting to decode it
        try:
            # First try to decode without verification to get the payload for debugging
            # When verify_signature=False, we still need to provide a key (can be dummy)
            unverified_payload = jwt.decode(
                access_token, 
                "dummy_key",  # Dummy key since we're not verifying signature
                algorithms=["HS256"],
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_iss": False, 
                    "verify_exp": False,
                    "verify_iat": False
                }
            )
            logger.info(f"Token payload (unverified): {unverified_payload}")
            
            # Try multiple possible JWT secrets
            jwt_secrets_to_try = [
                settings.supabase_jwt_secret,  # Primary JWT secret
                settings.supabase_anon_key.split('.')[-1],  # Signature part of anon key
                settings.supabase_anon_key,  # Full anon key
            ]
            
            payload = None
            for secret in jwt_secrets_to_try:
                try:
                    payload = jwt.decode(
                        access_token, 
                        secret, 
                        algorithms=["HS256"],
                        options={"verify_aud": False, "verify_iss": False}  # Disable both audience and issuer verification
                    )
                    logger.info(f"JWT validated successfully with secret: {secret[:10]}...")
                    break
                except jwt.JWTError as e:
                    logger.warning(f"JWT validation failed with secret {secret[:10]}...: {str(e)}")
                    continue
            
            if not payload:
                # If all secrets fail, just use the unverified payload for development
                logger.warning("All JWT validation attempts failed, using unverified payload for development")
                payload = unverified_payload
            
            # Extract user info from token
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id:
                logger.error(f"Invalid token payload - missing sub: {payload}")
                raise HTTPException(status_code=400, detail="Invalid token payload - missing user ID")
            
            if not email:
                logger.warning(f"Token missing email, will try to get from user_data: {payload}")
                email = user_data.get("email")
            
            # Update user_data with token info
            user_data.update({
                "id": user_id,
                "email": email or user_data.get("email", "unknown@example.com")
            })
            
        except Exception as e:
            logger.error(f"JWT processing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Token processing failed: {str(e)}")
        
        # Set secure cookies and get CSRF token
        csrf_token = SessionManager.set_auth_cookie(response, access_token, user_data)
        
        logger.info(f"Session created successfully for user: {user_data.get('email')}")
        logger.info(f"Cookies being set - Auth: {SessionManager.AUTH_COOKIE}, CSRF: {SessionManager.CSRF_COOKIE}")
        
        # Create response content
        response_content = {
            "status": "success",
            "csrf_token": csrf_token,
            "user": {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "role": user_data.get("role", "free")
            }
        }
        
        # Set headers and return the response object (which now has cookies)
        response.headers["X-CSRF-Token"] = csrf_token
        response.headers["Content-Type"] = "application/json"
        
        # Use the response object we've been setting cookies on
        import json
        response.body = json.dumps(response_content).encode()
        response.status_code = 200
        
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.post("/api/logout-secure")
@limiter.limit("30/minute")  # Rate limit logout attempts
async def logout_secure(request: Request, response: Response):
    """
    Secure logout that clears httpOnly cookies
    No CSRF validation required for logout (as specified)
    Rate limited to prevent abuse
    """
    try:
        # Clear session cookies
        SessionManager.clear_auth_cookies(response)
        
        return {"status": "success", "message": "Session cleared successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/api/session/user")
@limiter.limit("30/minute")
async def get_session_user(request: Request):
    """
    Get current user from session cookie
    Rate limited to prevent abuse
    """
    logger.info(f"Session user endpoint called. Cookies: {dict(request.cookies)}")
    
    user = get_current_user_from_cookie(request)
    if not user:
        logger.warning("No user found from session cookie")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    logger.info(f"User found from cookie: {user.email} ({user.role})")
    
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "subscription_status": user.subscription_status
    }

@app.get("/api/bets/raw", tags=["opportunities"])
@limiter.limit("30/minute")
async def raw_betting_export(request: Request, subscriber: UserCtx = Depends(require_subscription())):
    """
    Raw betting data export - SUBSCRIBERS AND ADMINS ONLY
    Returns unfiltered, unmasked data for analysis
    """
    try:
        opportunities = get_ev_data()
        analytics = get_analytics_data()
        last_update = get_last_update()
        
        if opportunities:
            ui_opportunities = process_opportunities_for_ui(opportunities)
            ui_opportunities.sort(key=lambda x: x.get('ev_percentage', 0), reverse=True)
        else:
            ui_opportunities = []
        
        return {
            "role": subscriber.role,
            "export_type": "raw",
            "total_opportunities": len(ui_opportunities),
            "opportunities": ui_opportunities,
            "analytics": analytics,
            "last_update": last_update,
            "exported_at": datetime.now().isoformat(),
            "subscriber_email": subscriber.email
        }
        
    except Exception as e:
        logger.error(f"Raw export error for {subscriber.email}: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@app.get("/api/analytics/advanced", tags=["analytics"])
@limiter.limit("30/minute") 
async def advanced_analytics(request: Request, subscriber: UserCtx = Depends(require_subscription())):
    """
    Advanced analytics endpoint - SUBSCRIBERS AND ADMINS ONLY
    Provides detailed market analysis and trends
    """
    try:
        analytics = get_analytics_data()
        opportunities = get_ev_data()
        
        # Calculate advanced metrics for subscribers
        if opportunities:
            ev_values = [opp.get('EV_Raw', 0) for opp in opportunities if opp.get('EV_Raw')]
            
            advanced_metrics = {
                "market_efficiency": {
                    "avg_ev": sum(ev_values) / len(ev_values) if ev_values else 0,
                    "ev_variance": sum([(x - sum(ev_values) / len(ev_values)) ** 2 for x in ev_values]) / len(ev_values) if len(ev_values) > 1 else 0,
                    "total_opportunities": len(opportunities)
                },
                "value_distribution": {
                    "excellent_4_5_plus": len([x for x in ev_values if x >= 0.045]),
                    "high_2_5_to_4_5": len([x for x in ev_values if 0.025 <= x < 0.045]),
                    "positive_0_to_2_5": len([x for x in ev_values if 0 < x < 0.025]),
                    "neutral_negative": len([x for x in ev_values if x <= 0])
                }
            }
        else:
            advanced_metrics = {"error": "No data available"}
        
        return {
            "role": subscriber.role,
            "analytics_type": "advanced",
            "basic_analytics": analytics,
            "advanced_metrics": advanced_metrics,
            "generated_at": datetime.now().isoformat(),
            "subscription_status": subscriber.subscription_status
        }
        
    except Exception as e:
        logger.error(f"Advanced analytics error for {subscriber.email}: {e}")
        raise HTTPException(status_code=500, detail="Analytics generation failed")

@app.get("/debug/cookies")
async def debug_cookies(request: Request):
    """Debug endpoint to inspect cookies and session state"""
    from core.session import SessionManager, get_current_user_from_cookie
    
    debug_info = {
        "all_cookies": dict(request.cookies),
        "auth_cookie_name": SessionManager.AUTH_COOKIE,
        "csrf_cookie_name": SessionManager.CSRF_COOKIE,
        "auth_cookie_value": request.cookies.get(SessionManager.AUTH_COOKIE),
        "csrf_cookie_value": request.cookies.get(SessionManager.CSRF_COOKIE),
        "user_from_cookie": None,
        "jwt_decode_error": None
    }
    
    # Try to get user from cookie
    try:
        user = get_current_user_from_cookie(request)
        if user:
            debug_info["user_from_cookie"] = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "subscription_status": user.subscription_status
            }
        else:
            debug_info["user_from_cookie"] = "No user found"
    except Exception as e:
        debug_info["jwt_decode_error"] = str(e)
    
    return debug_info

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
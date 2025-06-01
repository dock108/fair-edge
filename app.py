"""
FastAPI application for Sports Betting +EV Analyzer Dashboard
Serves the new HTML/CSS UI using Jinja2 templates
"""

from fastapi import FastAPI, Request, HTTPException, Depends
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

# Import database connections
from db import get_db, get_supabase, get_database_status

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
    with optional admin debugging features for development
    """
    try:
        # Get debug metrics if needed
        debug_metrics = get_debug_metrics() if is_admin_mode_enabled(request, admin) else None
        
        # Fetch data
        logger.info("Fetching real betting opportunities data...")
        raw_data = fetch_raw_odds_data()
        opportunities, analytics = process_opportunities(raw_data)
        
        # Log summary
        high_ev_count = analytics.get('high_ev_count', 0)
        positive_ev_count = analytics.get('positive_ev_count', 0)
        logger.info(f"Serving {len(opportunities)} opportunities ({high_ev_count} high EV, {positive_ev_count} positive EV)")
        
        # Process opportunities for UI
        ui_opportunities = process_opportunities_for_ui(opportunities)
        
        # Enhanced analytics for UI
        ui_analytics = {
            'total_opportunities': len(opportunities),
            'high_ev_count': high_ev_count,
            'positive_ev_count': positive_ev_count,
            'max_ev_percentage': round(analytics.get('max_ev', 0) * 100, 1),
            'avg_ev_percentage': round(analytics.get('avg_ev', 0) * 100, 1),
            'sports_breakdown': analytics.get('sports_breakdown', {}),
            'last_updated': datetime.now().strftime('%I:%M %p EST'),
            'processing_time': analytics.get('processing_time', 0)
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
                "status": "active",
                "duration": "30 minutes"
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
                "raw_data_sample": {
                    "total_events": raw_data.get('total_events', 0),
                    "fetch_time": raw_data.get('fetch_time', datetime.now()).strftime('%I:%M:%S %p'),
                    "status": raw_data.get('status', 'unknown')
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
                'processing_time': 0
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
    """API endpoint for getting opportunities data (for future AJAX updates)"""
    try:
        raw_data = fetch_raw_odds_data()
        if raw_data['status'] != 'success':
            return {"error": raw_data.get('error', 'Unknown error'), "opportunities": []}
        
        opportunities, analytics = process_opportunities(raw_data)
        ui_opportunities = process_opportunities_for_ui(opportunities)
        
        # Sort by EV percentage (highest first) for better user experience
        ui_opportunities.sort(key=lambda x: x['ev_percentage'], reverse=True)
        
        return {
            "opportunities": ui_opportunities,
            "analytics": analytics,
            "total_opportunities": len(ui_opportunities),
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in API route: {e}")
        return {"error": str(e), "opportunities": []}


@app.get("/health")
async def health_check():
    """Health check endpoint with data pipeline validation"""
    try:
        # Quick validation
        raw_data = fetch_raw_odds_data()
        status = "healthy" if raw_data['status'] == 'success' else "degraded"
        
        # Include database status
        db_status = await get_database_status()
        
        return {
            "status": status,
            "version": "2.1.0",
            "data_status": raw_data['status'],
            "total_events": raw_data.get('total_events', 0),
            "last_fetch": raw_data.get('fetch_time', '').isoformat() if raw_data.get('fetch_time') else None,
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "version": "2.1.0",
            "error": str(e)
        }


@app.get("/debug/profiles")
async def get_profiles_debug(db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint to verify Supabase database integration
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
            "message": "Successfully connected to Supabase database"
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
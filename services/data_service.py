"""
Data Service for handling data fetching patterns and processing
Centralizes all data-related logic that was duplicated across endpoints
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from services.redis_cache import get_ev_data, get_analytics_data, get_last_update
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities

logger = logging.getLogger(__name__)


class DataFetchResult:
    """Container for data fetch results with metadata"""
    
    def __init__(self, 
                 opportunities: List[Dict[str, Any]], 
                 analytics: Dict[str, Any],
                 data_source: str,
                 last_update: Optional[str] = None):
        self.opportunities = opportunities
        self.analytics = analytics
        self.data_source = data_source
        self.last_update = last_update or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "opportunities": self.opportunities,
            "analytics": self.analytics,
            "data_source": self.data_source,
            "last_update": self.last_update
        }


def fetch_opportunities_data() -> DataFetchResult:
    """
    Centralized data fetching with cache-first strategy
    Replaces the repeated cache/live data pattern throughout the codebase
    
    Returns:
        DataFetchResult: Contains opportunities, analytics, and metadata
    """
    logger.debug("Fetching opportunities data...")
    
    # Try cached data first
    cached_opportunities = get_ev_data()
    cached_analytics = get_analytics_data()
    last_update = get_last_update()
    
    if cached_opportunities and cached_analytics:
        logger.debug(f"Using cached data: {len(cached_opportunities)} opportunities")
        return DataFetchResult(
            opportunities=cached_opportunities,
            analytics=cached_analytics,
            data_source="cache",
            last_update=last_update
        )
    
    # Fallback to live data
    logger.info("Cache empty, fetching live data...")
    try:
        raw_data = fetch_raw_odds_data()
        if raw_data.get('status') == 'success':
            opportunities, analytics = process_opportunities(raw_data)
            logger.info(f"Fetched live data: {len(opportunities)} opportunities")
            return DataFetchResult(
                opportunities=opportunities,
                analytics=analytics,
                data_source="live"
            )
    except Exception as e:
        logger.error(f"Live data fetch failed: {e}")
    
    # Return empty result as fallback
    logger.warning("Both cache and live data failed, returning empty result")
    return DataFetchResult(
        opportunities=[],
        analytics={},
        data_source="error"
    )


def process_opportunities_for_ui(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform opportunities data from the backend into UI-friendly format
    This is imported from app.py to maintain the existing logic
    """
    # Import the existing function from app.py to avoid duplication
    from app import process_opportunities_for_ui as app_process_opportunities
    return app_process_opportunities(opportunities)


def apply_filters(opportunities: List[Dict[str, Any]], 
                  search: Optional[str] = None,
                  sport: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Apply search and sport filters to opportunities
    Centralizes the filtering logic that was duplicated
    """
    if not search and not sport:
        return opportunities
    
    filtered_opps = []
    search_term = search.lower() if search else None
    
    for opp in opportunities:
        # Search filter
        if search_term:
            searchable_text = " ".join([
                opp.get('event', ''),
                opp.get('bet_description', ''),
                opp.get('bet_type', ''),
                opp.get('best_odds_source', '')
            ]).lower()
            
            if search_term not in searchable_text:
                continue
        
        # Sport filter  
        if sport:
            # Map sport codes to identifiers that might appear in event names
            sport_keywords = {
                'americanfootball_nfl': ['nfl', 'football', 'patriots', 'cowboys', 'packers', 'steelers'],
                'basketball_nba': ['nba', 'basketball', 'lakers', 'warriors', 'celtics', 'nets'],
                'baseball_mlb': ['mlb', 'baseball', 'yankees', 'dodgers', 'red sox', 'giants'],
                'icehockey_nhl': ['nhl', 'hockey', 'rangers', 'bruins', 'kings', 'devils']
            }
            
            keywords = sport_keywords.get(sport, [sport])
            event_text = opp.get('event', '').lower()
            
            # Check if any sport keyword appears in the event
            if not any(keyword in event_text for keyword in keywords):
                continue
        
        filtered_opps.append(opp)
    
    return filtered_opps


def apply_role_based_filtering(opportunities: List[Dict[str, Any]], user_role: str) -> Dict[str, Any]:
    """
    Apply role-based filtering to opportunities
    This imports the existing function from app.py to maintain logic
    """
    # Import the existing function from app.py to avoid duplication
    from app import filter_opportunities_by_role
    return filter_opportunities_by_role(opportunities, user_role)


def sort_opportunities_by_ev(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort opportunities by EV percentage (highest first)
    Centralizes the sorting logic that was repeated
    """
    return sorted(opportunities, key=lambda x: x.get('ev_percentage', 0), reverse=True)


class OpportunityProcessor:
    """
    Main processor that handles the complete opportunity processing pipeline
    Replaces the repeated processing pattern throughout the codebase
    """
    
    def __init__(self, user_role: str):
        self.user_role = user_role
    
    def process(self, 
                search: Optional[str] = None,
                sport: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete processing pipeline: fetch -> process -> filter -> sort -> role-filter
        
        Returns:
            Dict containing filtered opportunities and metadata
        """
        # Fetch data
        data_result = fetch_opportunities_data()
        
        if not data_result.opportunities:
            return {
                **data_result.to_dict(),
                "filtered_response": {
                    "role": self.user_role,
                    "truncated": False,
                    "total_available": 0,
                    "shown": 0,
                    "opportunities": [],
                    "features": {}
                }
            }
        
        # Process for UI
        ui_opportunities = process_opportunities_for_ui(data_result.opportunities)
        
        # Apply filters
        if search or sport:
            ui_opportunities = apply_filters(ui_opportunities, search, sport)
        
        # Sort by EV
        ui_opportunities = sort_opportunities_by_ev(ui_opportunities)
        
        # Apply role-based filtering
        filtered_response = apply_role_based_filtering(ui_opportunities, self.user_role)
        
        # Combine results
        result = data_result.to_dict()
        result["filtered_response"] = filtered_response
        result["filters_applied"] = {
            "search": search,
            "sport": sport,
            "has_filters": bool(search or sport)
        }
        
        return result 
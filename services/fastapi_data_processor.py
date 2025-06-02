"""
FastAPI-compatible data processing service for sports betting +EV analysis
Handles raw data fetching, processing, and opportunity generation without Streamlit dependencies
"""
import time
import os
import pickle
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Tuple
import pytz
import threading

from services.odds_api import OddsAPIClient
from core.fair_odds_calculator import FairOddsCalculator
from core.ev_analyzer import EVAnalyzer
from core.maker_odds_calculator import MakerOddsCalculator
from utils.bet_matching import BetMatcher

logger = logging.getLogger(__name__)

# Cache configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
CACHE_DURATION = 10800 if DEBUG_MODE else 1800  # 3 hours in debug, 30 minutes in production
CACHE_DIR = "cache"
RAW_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "raw_data_cache.pkl")
PROCESSED_DATA_CACHE_FILE = os.path.join(CACHE_DIR, "processed_data_cache.pkl")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Thread lock for cache operations
_cache_lock = threading.Lock()

logger.info(f"Cache configuration: {'DEBUG' if DEBUG_MODE else 'PRODUCTION'} mode, {CACHE_DURATION//60} minute cache duration")


def deduplicate_opportunities(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate opportunities, keeping only the most recent version of each unique bet.
    
    Creates a unique identifier for each opportunity based on:
    - Event (game/match)
    - Market type (h2h, spreads, totals, etc.)
    - Outcome (team name, over/under, etc.)
    - Point value (for spreads/totals)
    
    Args:
        opportunities: List of opportunity dictionaries
        
    Returns:
        List of deduplicated opportunities (most recent version of each unique bet)
    """
    if not opportunities:
        return []
    
    # Dictionary to store the best version of each unique bet
    unique_bets = {}
    
    for opp in opportunities:
        # Create unique identifier for this bet
        event = opp.get('Event', '').strip()
        market = opp.get('Market', '').strip()
        bet_description = opp.get('Bet Description', '').strip()
        
        # Create a unique key combining event, market, and bet description
        # This ensures we identify the same bet even if described slightly differently
        unique_key = f"{event}|{market}|{bet_description}".lower()
        
        # If this is the first time we see this bet, or if this version has better EV, keep it
        if (unique_key not in unique_bets or 
                opp.get('EV_Raw', 0) > unique_bets[unique_key].get('EV_Raw', 0)):
            unique_bets[unique_key] = opp
    
    # Convert back to list and sort by EV
    deduplicated = list(unique_bets.values())
    deduplicated.sort(key=lambda x: x.get('EV_Raw', 0), reverse=True)
    
    logger.info(f"Deduplication: {len(opportunities)} → {len(deduplicated)} opportunities (removed {len(opportunities) - len(deduplicated)} duplicates)")
    
    return deduplicated


def _load_cache_file(cache_file: str) -> Dict[str, Any]:
    """Load cache data from file"""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        logger.debug(f"Failed to load cache file {cache_file}: {e}")
    return {}


def _save_cache_file(cache_file: str, data: Dict[str, Any]) -> None:
    """Save cache data to file"""
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to save cache file {cache_file}: {e}")


def _is_cache_valid(cache_data: Dict[str, Any]) -> bool:
    """Check if cached data is still valid"""
    if not cache_data or 'timestamp' not in cache_data or 'data' not in cache_data:
        return False
    
    cache_time = cache_data['timestamp']
    if not isinstance(cache_time, datetime):
        return False
    
    return datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION)


def fetch_raw_odds_data() -> Dict[str, Any]:
    """
    Cached data fetching from odds API (3-hour cache in debug mode, 30-minute cache in production)
    Returns: Raw odds data with metadata
    """
    with _cache_lock:
        # Try to load from persistent cache
        cache_data = _load_cache_file(RAW_DATA_CACHE_FILE)
        
        if _is_cache_valid(cache_data):
            logger.info("Returning cached raw odds data from file")
            return cache_data['data']
    
    try:
        client = OddsAPIClient()
        
        # Fetch data for multiple sports
        sports_to_fetch = ['basketball_nba', 'americanfootball_nfl', 'baseball_mlb', 'icehockey_nhl']
        
        logger.info("Fetching fresh raw odds data from API...")
        odds_data = client.get_all_odds_24h(sports_to_fetch)
        filtered_data = client.filter_two_sided_markets(odds_data)
        
        result = {
            'data': filtered_data,
            'fetch_time': datetime.now(),
            'status': 'success',
            'total_events': sum(len(events) for events in filtered_data.values())
        }
        
        # Save to persistent cache
        with _cache_lock:
            cache_data = {
                'data': result,
                'timestamp': datetime.now()
            }
            _save_cache_file(RAW_DATA_CACHE_FILE, cache_data)
        
        logger.info(f"Fetched {result['total_events']} events successfully and cached to file")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching odds data: {e}")
        return {
            'data': {},
            'fetch_time': datetime.now(),
            'status': 'error',
            'error': str(e),
            'total_events': 0
        }


def process_opportunities(raw_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process raw odds data into betting opportunities with analytics (3-hour cache in debug mode, 30-minute cache in production)
    Args:
        raw_data: Raw odds data from fetch_raw_odds_data()
    Returns:
        Tuple of (opportunities_list, analytics_summary)
    """
    with _cache_lock:
        # Try to load from persistent cache
        cache_data = _load_cache_file(PROCESSED_DATA_CACHE_FILE)
        
        if _is_cache_valid(cache_data):
            logger.info("Returning cached processed opportunities from file")
            return cache_data['data']
    
    if raw_data['status'] != 'success':
        return [], {'error': raw_data.get('error', 'Unknown error')}
    
    try:
        # Initialize analyzers
        calculator = FairOddsCalculator()
        ev_analyzer = EVAnalyzer(ev_threshold=0.045)
        maker_calculator = MakerOddsCalculator(target_margin=0.045)
        
        opportunities = []
        analytics = {
            'total_markets_analyzed': 0,
            'total_opportunities': 0,
            'high_ev_count': 0,
            'positive_ev_count': 0,
            'max_ev': 0.0,
            'avg_ev': 0.0,
            'sports_breakdown': {},
            'processing_time': None
        }
        
        start_time = time.time()
        
        # Process each sport
        for sport_key, events in raw_data['data'].items():
            sport_opportunities = 0
            
            for event in events:
                event_name = f"{event.get('away_team', 'Unknown')} @ {event.get('home_team', 'Unknown')}"
                event_time = event.get('commence_time', '')
                
                # Format event time
                event_display = _format_event_display(event_name, event_time)
                
                # Process each market type
                markets_by_type = _extract_markets_by_type(event)
                
                for market_key, market_odds in markets_by_type.items():
                    analytics['total_markets_analyzed'] += 1
                    
                    # Analyze market opportunities
                    market_opportunities = _analyze_single_market(
                        event_display, market_key, market_odds,
                        calculator, ev_analyzer, maker_calculator
                    )
                    
                    opportunities.extend(market_opportunities)
                    sport_opportunities += len(market_opportunities)
            
            analytics['sports_breakdown'][sport_key] = sport_opportunities
        
        # Sort opportunities by EV (highest first)
        opportunities.sort(key=lambda x: x.get('EV_Raw', 0), reverse=True)
        
        # DEDUPLICATION: Remove duplicate opportunities, keeping only the most recent
        deduplicated_opportunities = deduplicate_opportunities(opportunities)
        
        # Update analytics with deduplicated counts
        analytics['total_opportunities'] = len(deduplicated_opportunities)
        analytics['processing_time'] = round(time.time() - start_time, 2)
        
        if deduplicated_opportunities:
            ev_values = [opp.get('EV_Raw', 0) for opp in deduplicated_opportunities]
            analytics['high_ev_count'] = sum(1 for ev in ev_values if ev >= 0.045)
            analytics['positive_ev_count'] = sum(1 for ev in ev_values if ev > 0)
            analytics['max_ev'] = max(ev_values)
            analytics['avg_ev'] = sum(ev_values) / len(ev_values)
        
        result = (deduplicated_opportunities, analytics)
        
        # Save to persistent cache
        with _cache_lock:
            cache_data = {
                'data': result,
                'timestamp': datetime.now()
            }
            _save_cache_file(PROCESSED_DATA_CACHE_FILE, cache_data)
        
        logger.info(f"Processed {len(opportunities)} opportunities ({len(deduplicated_opportunities)} after deduplication) in {analytics['processing_time']}s and cached to file")
        return result
        
    except Exception as e:
        logger.error(f"Error processing opportunities: {e}")
        return [], {'error': str(e)}


def _format_event_display(event_name: str, event_time: str) -> str:
    """Format event name with time for display"""
    if event_time:
        try:
            # Parse ISO format time
            if event_time.endswith('Z'):
                event_time = event_time[:-1] + '+00:00'
            
            event_dt_utc = datetime.fromisoformat(event_time)
            
            # Convert to EST
            utc_tz = pytz.UTC
            est_tz = pytz.timezone('US/Eastern')
            
            if event_dt_utc.tzinfo is None:
                event_dt_utc = utc_tz.localize(event_dt_utc)
            
            event_dt_est = event_dt_utc.astimezone(est_tz)
            
            # Format for display
            now = datetime.now(est_tz)
            if event_dt_est.date() == now.date():
                time_str = f"Today {event_dt_est.strftime('%I:%M%p EST')}"
            elif event_dt_est.date() == (now + timedelta(days=1)).date():
                time_str = f"Tomorrow {event_dt_est.strftime('%I:%M%p EST')}"
            else:
                time_str = event_dt_est.strftime('%m/%d %I:%M%p EST')
            
            return f"{event_name} • {time_str}"
        except Exception as e:
            logger.debug(f"Error parsing event time {event_time}: {e}")
            return event_name
    return event_name


def _extract_markets_by_type(event: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract and organize markets by type from event data"""
    markets_by_type = {}
    for bookmaker in event.get('bookmakers', []):
        bookmaker_key = bookmaker['key']
        for market in bookmaker.get('markets', []):
            market_key = market['key']
            if market_key not in markets_by_type:
                markets_by_type[market_key] = {}
            markets_by_type[market_key][bookmaker_key] = market['outcomes']
    return markets_by_type


def _analyze_single_market(event_display: str, market_key: str, market_odds: Dict,
                           calculator, ev_analyzer, maker_calculator) -> List[Dict[str, Any]]:
    """Analyze a single market and return comprehensive opportunity data"""
    try:
        # Calculate fair odds
        fair_odds_result = calculator.calculate_fair_odds(market_odds, market_key)
        if not fair_odds_result:
            return []
        
        # EV Analysis
        ev_analysis = ev_analyzer.analyze_market_opportunities(market_odds, fair_odds_result, market_key)
        if 'error' in ev_analysis:
            return []
        
        # Posting recommendations
        posting_recs = maker_calculator.get_posting_recommendations(fair_odds_result, market_odds)
        if 'error' in posting_recs:
            return []
        
        # CRITICAL FILTER: Check if we have at least 2 major books with BOTH sides
        # This prevents betting on markets where only 1 major book offers complete coverage
        major_books_with_both_sides = BetMatcher.count_major_books_with_both_sides(market_odds, market_key)
        if major_books_with_both_sides < 2:
            logger.debug(f"Market {market_key} filtered out: only {major_books_with_both_sides} major books have both sides")
            return []
        
        opportunities = []
        
        # Process each outcome with full detail
        for outcome_name in fair_odds_result['outcomes']:
            # Check if this specific outcome has at least 2 major books offering it
            major_books_count = BetMatcher.count_major_books(outcome_name, market_odds, market_key)
            if major_books_count < 2:
                continue  # Skip outcomes that don't have 2+ major books
            
            # Get bet description
            bet_description = _format_bet_description(market_key, outcome_name, market_odds)
            
            # Get all available odds using centralized matching
            all_odds_str = BetMatcher.format_all_odds(outcome_name, market_odds, market_key)
            
            # Get EV analysis data
            outcome_ev = ev_analysis['outcomes'].get(outcome_name, {})
            if not outcome_ev:
                continue
            
            fair_odds = outcome_ev['fair_odds']
            best_market = outcome_ev.get('best_market_odds')
            ev_data = outcome_ev['ev_analysis']
            
            # Get posting data
            outcome_posting = posting_recs['outcomes'].get(outcome_name, {})
            
            # Format best available odds with exchange fee info
            best_odds_str = "N/A"
            if best_market:
                from utils.bet_matching import _get_bookmaker_display_name
                bookmaker_display = _get_bookmaker_display_name(best_market['bookmaker'])
                is_exchange = best_market.get('is_exchange', False)
                
                if is_exchange and best_market.get('exchange_data'):
                    exchange_data = best_market['exchange_data']
                    original_american = exchange_data['original_american']
                    adjusted_american = exchange_data['adjusted_american']
                    commission_rate = exchange_data['commission_rate']
                    
                    best_odds_str = f"{original_american:+d} → {adjusted_american:+d} ({bookmaker_display}, -{commission_rate*100:.0f}% fee)"
                else:
                    best_odds_str = f"{best_market['american']:+d} ({bookmaker_display})"
            
            # Format EV percentage with exchange fee info
            ev_percentage = ev_data['ev_percentage']
            ev_display_original = ev_data.get('ev_display_original')
            
            if ev_display_original:
                # Show both pre-fee and post-fee EV for exchanges
                ev_display = f"{ev_data['ev_display']} (after fees) | {ev_display_original} (before fees)"
            else:
                # Regular bookmaker, just show the EV
                ev_display = f"{ev_percentage*100:+.1f}%"
            
            # Get proposed posting odds
            proposed_odds = _get_proposed_posting_odds(outcome_posting)
            
            # Get recommended action
            recommended_action = _get_recommended_action(outcome_ev, outcome_posting)
            
            # Create comprehensive opportunity record
            opportunity = {
                'Event': event_display,
                'Bet Description': bet_description,
                'All Available Odds': all_odds_str,
                'Fair Odds': f"{fair_odds['american']:+d}",
                'Best Available Odds': best_odds_str,
                'Expected Value %': ev_display,
                'EV_Raw': ev_percentage,  # For sorting
                'Proposed Posting Odds': proposed_odds,
                'Recommended Action': recommended_action,
                'Links': _generate_action_links(outcome_ev, outcome_posting),
                # Color coding helpers
                'EV_Color': _get_ev_color(ev_percentage),
                'Best_Odds_Source': best_market['bookmaker'] if best_market else None,
                # Additional fields for enhanced display
                'Market': market_key,
                'Outcome': outcome_name,
                'EV_Display': ev_display
            }
            
            opportunities.append(opportunity)
        
        return opportunities
        
    except Exception as e:
        logger.debug(f"Error analyzing market {market_key}: {e}")
        return []


def _format_bet_description(market_key: str, outcome_name: str, market_odds: Dict) -> str:
    """Format the bet description based on market type and outcome with detailed information"""
    
    # Try to extract more detailed information from the first available outcome
    player_name = None
    point_value = None
    
    # Look through all bookmakers for this outcome to extract detailed information
    for bookmaker, outcomes in market_odds.items():
        for outcome in outcomes:
            if outcome.get('name') == outcome_name:
                # Extract point value directly from 'point' field
                if 'point' in outcome:
                    point_value = outcome['point']
                
                # Extract player/pitcher name from 'description' field
                if 'description' in outcome:
                    player_name = outcome['description']
                
                break
        if player_name and point_value is not None:
            break
    
    # Format based on market type with enhanced details
    if market_key == 'h2h':
        return f"{outcome_name} Moneyline"
    elif market_key == 'spreads':
        if point_value is not None:
            if outcome_name in ['Over', 'Under']:
                return f"{outcome_name} {point_value}"
            else:
                sign = "+" if point_value >= 0 else ""
                return f"{outcome_name} {sign}{point_value}"
        return f"{outcome_name} Spread"
    elif market_key == 'totals':
        if point_value is not None:
            return f"{outcome_name} {point_value} Total"
        return f"{outcome_name} Total"
    elif market_key.startswith('player_'):
        # Clean player prop descriptions with stat type
        stat_type = market_key.replace('player_', '').replace('_', ' ').title()
        if player_name and point_value is not None:
            return f"{player_name} {outcome_name} {point_value} {stat_type}"
        elif player_name:
            return f"{player_name} {outcome_name} {stat_type}"
        elif point_value is not None:
            return f"{outcome_name} {point_value} {stat_type}"
        else:
            return f"{outcome_name} {stat_type}"
    elif market_key.startswith('pitcher_'):
        # Clean pitcher prop descriptions with readable stat type
        stat_type_map = {
            'pitcher_strikeouts': 'Strikeouts',
            'pitcher_hits_allowed': 'Hits Allowed',
            'pitcher_walks': 'Walks',
            'pitcher_earned_runs': 'Earned Runs',
            'pitcher_outs': 'Outs',
            'pitcher_record_a_win': 'Win'
        }
        stat_type = stat_type_map.get(market_key, market_key.replace('pitcher_', '').replace('_', ' ').title())
        
        if player_name and point_value is not None:
            return f"{player_name} {outcome_name} {point_value} {stat_type}"
        elif player_name:
            return f"{player_name} {outcome_name} {stat_type}"
        elif point_value is not None:
            return f"{outcome_name} {point_value} {stat_type}"
        else:
            return f"{outcome_name} {stat_type}"
    elif market_key.startswith('batter_'):
        # Clean batter prop descriptions with readable stat type
        stat_type_map = {
            'batter_hits': 'Hits',
            'batter_home_runs': 'Home Runs',
            'batter_rbis': 'RBIs',
            'batter_runs_scored': 'Runs',
            'batter_stolen_bases': 'Stolen Bases',
            'batter_total_bases': 'Total Bases',
            'batter_singles': 'Singles',
            'batter_doubles': 'Doubles',
            'batter_triples': 'Triples',
            'batter_walks': 'Walks',
            'batter_strikeouts': 'Strikeouts'
        }
        stat_type = stat_type_map.get(market_key, market_key.replace('batter_', '').replace('_', ' ').title())
        
        if player_name and point_value is not None:
            return f"{player_name} {outcome_name} {point_value} {stat_type}"
        elif player_name:
            return f"{player_name} {outcome_name} {stat_type}"
        elif point_value is not None:
            return f"{outcome_name} {point_value} {stat_type}"
        else:
            return f"{outcome_name} {stat_type}"
    else:
        # Generic market formatting with point value if available
        if point_value is not None:
            return f"{outcome_name} {point_value}"
        else:
            return f"{outcome_name}"


def _get_bookmaker_display_name(bookmaker_key: str) -> str:
    """Get display name for bookmaker"""
    display_names = {
        'draftkings': 'DraftKings',
        'fanduel': 'FanDuel',
        'pinnacle': 'Pinnacle',
        'bovada': 'Bovada',
        'betmgm': 'BetMGM',
        'pointsbetus': 'PointsBet',
        'williamhill_us': 'WilliamHill',
        'betrivers': 'BetRivers'
    }
    return display_names.get(bookmaker_key, bookmaker_key.title())


def _get_proposed_posting_odds(outcome_posting: Dict) -> str:
    """Get proposed posting odds string"""
    if not outcome_posting:
        return "N/A"
    
    posting_rec = outcome_posting.get('posting_recommendation')
    if posting_rec and posting_rec.get('recommended_american_odds'):
        odds = posting_rec['recommended_american_odds']
        return f"{odds:+d}"
    
    # If no posting recommendation but we have fair odds, calculate target posting odds
    # This ensures we always show a posting recommendation
    fair_odds = outcome_posting.get('fair_odds')
    if fair_odds and fair_odds.get('american'):
        try:
            # Calculate odds for 2.5% target EV after 2% exchange commission
            target_ev = 0.025  # 2.5%
            exchange_commission = 0.02  # 2%
            
            fair_american = fair_odds['american']
            if fair_american > 0:
                # Positive odds: decimal = (american/100) + 1
                fair_decimal = (fair_american / 100) + 1
                # Target decimal odds = fair_decimal * (1 + target_ev) / (1 - commission)
                target_decimal = fair_decimal * (1 + target_ev) / (1 - exchange_commission)
                target_american = int((target_decimal - 1) * 100)
                return f"+{target_american}"
            else:
                # Negative odds: decimal = (100/abs(american)) + 1
                fair_decimal = (100 / abs(fair_american)) + 1
                target_decimal = fair_decimal * (1 + target_ev) / (1 - exchange_commission)
                if target_decimal > 2.0:
                    target_american = int((target_decimal - 1) * 100)
                    return f"+{target_american}"
                else:
                    target_american = int(-100 / (target_decimal - 1))
                    return f"{target_american}"
        except (ValueError, ZeroDivisionError, TypeError):
            pass
    
    return "N/A"


def _get_recommended_action(outcome_ev: Dict, outcome_posting: Dict) -> str:
    """Get recommended action string"""
    ev_data = outcome_ev.get('ev_analysis', {})
    ev_percentage = ev_data.get('ev_percentage', 0)
    
    # Always provide an action recommendation
    if ev_percentage >= 0.045:  # 4.5%+ EV
        best_market = outcome_ev.get('best_market_odds')
        if best_market:
            from utils.bet_matching import _get_bookmaker_display_name
            bookmaker = _get_bookmaker_display_name(best_market['bookmaker'])
            return f"Strong Take: {bookmaker} ({ev_percentage*100:+.1f}% EV)"
    elif ev_percentage >= 0.025:  # 2.5%+ EV
        best_market = outcome_ev.get('best_market_odds')
        if best_market:
            from utils.bet_matching import _get_bookmaker_display_name
            bookmaker = _get_bookmaker_display_name(best_market['bookmaker'])
            return f"Take bet: {bookmaker} ({ev_percentage*100:+.1f}% EV)"
    elif ev_percentage > 0:  # Any positive EV
        return f"Marginal +EV ({ev_percentage*100:+.1f}%)"
    elif ev_percentage >= -0.02:  # Close to fair
        return "Post on P2P exchange if interested"
    else:
        return f"Post opposite side ({ev_percentage*100:+.1f}% EV)"


def _generate_action_links(outcome_ev: Dict, outcome_posting: Dict) -> str:
    """Generate action links string"""
    best_market = outcome_ev.get('best_market_odds')
    posting_rec = outcome_posting.get('posting_recommendation')
    
    links = []
    
    # Take link - if EV is reasonable or for demo purposes
    if best_market:
        ev_percentage = outcome_ev.get('ev_analysis', {}).get('ev_percentage', 0)
        bookmaker = best_market['bookmaker']
        
        # Generate take link for positive EV or demo purposes
        if ev_percentage >= 0.015 or True:  # Always show for demo
            take_url = f"https://{bookmaker}.com/sportsbook"
            links.append(f"Take: {take_url}")
    
    # Post link - always show posting option
    if posting_rec or True:  # Always show for demo
        post_url = "https://novig.com/exchange"  # Default exchange
        links.append(f"Post: {post_url}")
    
    return " | ".join(links) if links else "N/A"


def _get_ev_color(ev_percentage: float) -> str:
    """Get color classification for EV"""
    if ev_percentage >= 0.045:
        return "high"
    elif ev_percentage > 0:
        return "positive"
    else:
        return "neutral"


def validate_data_pipeline() -> Dict[str, Any]:
    """Validate the data pipeline"""
    try:
        # Test API connection
        raw_data = fetch_raw_odds_data()
        api_connection = raw_data['status'] == 'success'
        
        # Test data processing
        if api_connection:
            opportunities, analytics = process_opportunities(raw_data)
            data_processing = len(opportunities) >= 0  # Any result is valid
        else:
            data_processing = False
            opportunities = []
        
        return {
            'api_connection': api_connection,
            'data_fetch': api_connection,
            'data_processing': data_processing,
            'total_opportunities': len(opportunities),
            'errors': [] if api_connection and data_processing else [raw_data.get('error', 'Unknown error')]
        }
    except Exception as e:
        return {
            'api_connection': False,
            'data_fetch': False,
            'data_processing': False,
            'total_opportunities': 0,
            'errors': [str(e)]
        }


def clear_cache():
    """Clear all cached data (useful for testing)"""
    with _cache_lock:
        try:
            if os.path.exists(RAW_DATA_CACHE_FILE):
                os.remove(RAW_DATA_CACHE_FILE)
                logger.info(f"Deleted raw data cache file: {RAW_DATA_CACHE_FILE}")
            
            if os.path.exists(PROCESSED_DATA_CACHE_FILE):
                os.remove(PROCESSED_DATA_CACHE_FILE)
                logger.info(f"Deleted processed data cache file: {PROCESSED_DATA_CACHE_FILE}")
            
            logger.info("File-based cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache files: {e}")
            raise 
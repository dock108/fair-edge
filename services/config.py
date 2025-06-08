"""
Configuration settings for the Sports Betting +EV Analyzer
"""
import os
from dotenv import load_dotenv
from core.config.sports import SportsConfig

# Load environment variables
load_dotenv()

# The Odds API Configuration
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Refresh settings
REFRESH_INTERVAL_MINUTES = int(os.getenv('REFRESH_INTERVAL_MINUTES', 5))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Import sports configuration from canonical location
sports_config = SportsConfig()

# Bookmaker configuration - imported from canonical location
BOOKMAKERS = sports_config.BOOKMAKERS

# Featured markets (available on main /sports/{sport}/odds endpoint)
FEATURED_MARKETS = sports_config.FEATURED_MARKETS

# Additional markets (require /events/{eventId}/odds endpoint)
ADDITIONAL_MARKETS = sports_config.ADDITIONAL_MARKETS

# Sport-specific featured markets (for main endpoint)
SPORT_FEATURED_MARKETS = {
    'americanfootball_nfl': FEATURED_MARKETS,
    'basketball_nba': FEATURED_MARKETS,
    'basketball_ncaab': FEATURED_MARKETS,
    'baseball_mlb': FEATURED_MARKETS,
    'icehockey_nhl': FEATURED_MARKETS,
    'soccer_epl': FEATURED_MARKETS,
    'soccer_uefa_champs_league': FEATURED_MARKETS
}

# Legacy configurations
DEFAULT_MARKETS = FEATURED_MARKETS
MARKETS = DEFAULT_MARKETS

# Sports to monitor (will be dynamically fetched from API)
SUPPORTED_SPORTS = sports_config.SUPPORTED_SPORTS

# Exchange commission rates (for market making calculations)
EXCHANGE_COMMISSIONS = sports_config.EXCHANGE_COMMISSIONS

# Maker edge margin (additional profit margin for market making)
MAKER_EDGE_MARGIN = sports_config.MAKER_EDGE_MARGIN

# Major books for market validation (must have at least 2 of these for a valid market)
MAJOR_BOOKS = sports_config.MAJOR_BOOKS

# Exchange platforms
EXCHANGES = sports_config.EXCHANGES

# All supported bookmakers
ALL_BOOKMAKERS = sports_config.ALL_BOOKMAKERS 
"""
Odds API Client for fetching real-time sports betting odds
Integrates with The Odds API v4 to retrieve odds from specified bookmakers
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz
import requests

from core.config.sports import SportsConfig
from core.settings import settings

# Map settings to old variable names for backward compatibility
ODDS_API_KEY = settings.odds_api_key
ODDS_API_BASE_URL = settings.odds_api_base_url
DEBUG = settings.is_debug

# Import configuration constants
SUPPORTED_SPORTS = SportsConfig.SUPPORTED_SPORTS
BOOKMAKERS = SportsConfig.BOOKMAKERS
FEATURED_MARKETS = SportsConfig.FEATURED_MARKETS
SPORT_FEATURED_MARKETS = SportsConfig.ADDITIONAL_MARKETS  # This is the sport-specific markets dict
ADDITIONAL_MARKETS = SportsConfig.ADDITIONAL_MARKETS
MAJOR_BOOKS = SportsConfig.MAJOR_BOOKS

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


class OddsAPIClient:
    """Client for interacting with The Odds API v4"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ODDS_API_KEY
        self.base_url = ODDS_API_BASE_URL
        self.session = requests.Session()

        if not self.api_key:
            raise ValueError("API key is required. Set ODDS_API_KEY environment variable.")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to The Odds API with error handling"""
        url = f"{self.base_url}/{endpoint}"
        params["apiKey"] = self.api_key

        try:
            logger.debug(f"Making request to {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=30)

            # Log quota usage from headers
            if "x-requests-remaining" in response.headers:
                remaining = response.headers.get("x-requests-remaining")
                used = response.headers.get("x-requests-used")
                last_cost = response.headers.get("x-requests-last")
                logger.info(
                    f"API Quota - Remaining: {remaining}, Used: {used}, Last Cost: {last_cost}"
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.error("Rate limit exceeded. Please wait before making more requests.")
            elif response.status_code == 401:
                logger.error("Invalid API key or unauthorized access.")
            else:
                logger.error(f"HTTP error {response.status_code}: {e}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def get_active_sports(self) -> List[Dict[str, Any]]:
        """Get list of active sports from The Odds API"""
        logger.info("Fetching active sports...")

        params = {"all": "false"}  # Only active sports
        data = self._make_request("sports", params)

        if data:
            active_sports = [sport for sport in data if sport.get("active", False)]
            logger.info(f"Found {len(active_sports)} active sports")
            return active_sports

        return []

    def get_upcoming_events_24h(self, sport_key: str) -> List[Dict[str, Any]]:
        """Get events for a specific sport starting in the next 24 hours"""
        now = datetime.now(pytz.UTC)
        end_time = now + timedelta(hours=24)

        # Format times for API (ISO 8601) - remove microseconds for cleaner format
        commence_time_from = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        commence_time_to = end_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        logger.debug(
            f"Fetching events for {sport_key} from {commence_time_from} to {commence_time_to}"
        )

        params = {
            "commenceTimeFrom": commence_time_from,
            "commenceTimeTo": commence_time_to,
            "oddsFormat": "decimal",  # Use decimal odds for easier calculations
            "dateFormat": "iso",
        }

        endpoint = f"sports/{sport_key}/odds"
        data = self._make_request(endpoint, params)

        if data:
            logger.info(f"Found {len(data)} upcoming events for {sport_key}")
            return data

        return []

    def get_odds_for_event(
        self, sport_key: str, event_id: str, markets: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed odds for a specific event with all markets"""
        if markets is None:
            markets = SPORT_FEATURED_MARKETS.get(sport_key, FEATURED_MARKETS)

        # Get bookmaker keys for our 5 platforms
        bookmaker_keys = [bm["key"] for bm in BOOKMAKERS.values()]

        params = {
            "regions": "us,us_ex,eu",  # Include us_ex for exchanges
            "markets": ",".join(markets),
            "bookmakers": ",".join(bookmaker_keys),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        endpoint = f"sports/{sport_key}/events/{event_id}/odds"
        data = self._make_request(endpoint, params)

        if data:
            logger.debug(
                f"Retrieved odds for event {event_id} with {len(data.get('bookmakers', []))} bookmakers"
            )
            return data

        return None

    def get_all_odds_24h(self, sport_keys: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all odds for events in the next 24 hours across specified sports"""
        if sport_keys is None:
            # Get active sports and filter to our supported ones
            active_sports = self.get_active_sports()
            active_sport_keys = [sport["key"] for sport in active_sports]
            sport_keys = [key for key in SUPPORTED_SPORTS if key in active_sport_keys]

        logger.info(f"Fetching odds for sports: {sport_keys}")

        all_odds = {}
        bookmaker_keys = [bm["key"] for bm in BOOKMAKERS.values()]

        for sport_key in sport_keys:
            logger.info(f"Processing sport: {sport_key}")

            # Get events with basic odds first
            now = datetime.now(pytz.UTC)
            end_time = now + timedelta(hours=24)

            params = {
                "commenceTimeFrom": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "commenceTimeTo": end_time.replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "regions": "us,us_ex,eu",  # Include us_ex for exchanges
                "markets": ",".join(FEATURED_MARKETS),  # Start with basic markets only
                "bookmakers": ",".join(bookmaker_keys),
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            }

            endpoint = f"sports/{sport_key}/odds"
            sport_odds = self._make_request(endpoint, params)

            if sport_odds:
                # Enrich events with additional markets if available
                enriched_events = []
                for event in sport_odds:
                    enriched_event = self._enrich_event_with_additional_markets(event, sport_key)
                    enriched_events.append(enriched_event)

                all_odds[sport_key] = enriched_events
                logger.info(f"Retrieved {len(enriched_events)} events for {sport_key}")
            else:
                all_odds[sport_key] = []
                logger.warning(f"No odds retrieved for {sport_key}")

        total_events = sum(len(events) for events in all_odds.values())
        logger.info(f"Total events retrieved: {total_events}")

        return all_odds

    def filter_two_sided_markets(
        self, odds_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter to only include high-quality two-sided markets with proper coverage
        Requirements:
        1. At least 2 of the 3 major books (Pinnacle, DraftKings, FanDuel) must offer odds
        2. Must have clear opposing outcomes (two-sided market)
        3. Odds must be valid and recent
        """
        filtered_data = {}

        for sport_key, events in odds_data.items():
            filtered_events = []

            for event in events:
                filtered_event = event.copy()
                filtered_bookmakers = []

                # Group markets by type across all bookmakers for this event
                markets_by_type = {}
                for bookmaker in event.get("bookmakers", []):
                    bookmaker_key = bookmaker["key"]
                    for market in bookmaker.get("markets", []):
                        market_key = market["key"]
                        if market_key not in markets_by_type:
                            markets_by_type[market_key] = {}
                        markets_by_type[market_key][bookmaker_key] = market

                # Filter each market type based on our criteria
                valid_markets_by_bookmaker = {}
                for market_key, bookmaker_markets in markets_by_type.items():
                    if self._is_market_valid_for_analysis(market_key, bookmaker_markets):
                        # Add valid markets to each bookmaker's data
                        for bookmaker_key, market_data in bookmaker_markets.items():
                            if bookmaker_key not in valid_markets_by_bookmaker:
                                valid_markets_by_bookmaker[bookmaker_key] = []
                            valid_markets_by_bookmaker[bookmaker_key].append(market_data)

                # Rebuild bookmaker data with only valid markets
                for bookmaker in event.get("bookmakers", []):
                    bookmaker_key = bookmaker["key"]
                    if bookmaker_key in valid_markets_by_bookmaker:
                        filtered_bookmaker = bookmaker.copy()
                        filtered_bookmaker["markets"] = valid_markets_by_bookmaker[bookmaker_key]
                        filtered_bookmakers.append(filtered_bookmaker)

                # Only include event if it has valid markets
                if filtered_bookmakers:
                    filtered_event["bookmakers"] = filtered_bookmakers
                    filtered_events.append(filtered_event)
                    logger.debug(
                        f"Event {event.get('id', 'unknown')} passed filtering with {len(filtered_bookmakers)} bookmakers"
                    )
                else:
                    logger.debug(
                        f"Event {event.get('id', 'unknown')} filtered out - no valid markets"
                    )

            filtered_data[sport_key] = filtered_events
            logger.info(
                f"Filtered {sport_key}: {len(filtered_events)} events (from {len(events)} original)"
            )

        return filtered_data

    def _is_market_valid_for_analysis(
        self, market_key: str, bookmaker_markets: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Check if a market meets our criteria for analysis
        1. At least 2 major books must offer this market
        2. Market must be truly two-sided
        3. Odds must be valid
        """
        # Check major book coverage requirement
        major_books_offering = []
        for major_book in MAJOR_BOOKS:
            if major_book in bookmaker_markets:
                market_data = bookmaker_markets[major_book]
                if self._has_valid_odds_entries(market_data):
                    major_books_offering.append(major_book)

        if len(major_books_offering) < 2:
            logger.debug(
                f"Market {market_key} rejected: only {len(major_books_offering)} major books offering"
            )
            return False

        # Check if market is truly two-sided using the best available data
        # Use data from a major book that offers this market
        sample_market = bookmaker_markets[major_books_offering[0]]
        if not self._is_two_sided_market(market_key, sample_market.get("outcomes", [])):
            logger.debug(f"Market {market_key} rejected: not two-sided")
            return False

        logger.debug(
            f"Market {market_key} accepted: {len(major_books_offering)} major books, two-sided"
        )
        return True

    def _has_valid_odds_entries(self, market_data: Dict[str, Any]) -> bool:
        """
        Check if market data has valid, recent odds entries
        """
        outcomes = market_data.get("outcomes", [])
        if not outcomes:
            return False

        # Check that all outcomes have valid numeric odds
        for outcome in outcomes:
            price = outcome.get("price")
            if not isinstance(price, (int, float)) or price <= 1.0:
                logger.debug(f"Invalid price found: {price}")
                return False

        # Check for recent update timestamp
        last_update = market_data.get("last_update")
        if last_update:
            try:
                from datetime import datetime

                import pytz

                # Parse the timestamp
                if last_update.endswith("Z"):
                    update_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                else:
                    update_time = datetime.fromisoformat(last_update)

                # Check if updated within last hour (reasonable freshness)
                now = datetime.now(pytz.UTC)
                if (now - update_time.replace(tzinfo=pytz.UTC)).total_seconds() > 3600:
                    logger.debug(f"Stale odds detected: last updated {last_update}")
                    return False

            except Exception as e:
                logger.debug(f"Could not parse timestamp {last_update}: {e}")
                # Don't reject just for timestamp parsing issues
                pass

        return True

    def _is_two_sided_market(self, market_key: str, outcomes: List[Dict[str, Any]]) -> bool:
        """
        Determine if a market is two-sided (has clear opposite outcomes)
        Enhanced logic to ensure we only analyze markets with true opposing outcomes
        """
        if not outcomes or len(outcomes) < 2:
            return False

        # Featured market types with clear two-sided structure
        two_sided_markets = {
            "h2h",  # Head-to-head (team A vs team B)
            "spreads",  # Point spreads (team A +X vs team B -X)
            "totals",  # Over/under totals
        }

        # For main markets, ensure exactly 2 outcomes with different names
        if market_key in two_sided_markets:
            if len(outcomes) != 2:
                return False

            # Check that outcomes have different names (not duplicates)
            outcome_names = [outcome.get("name", "").strip().lower() for outcome in outcomes]
            if len(set(outcome_names)) != 2:
                return False

            # For spreads and totals, ensure we have opposing outcomes
            if market_key == "spreads":
                # Should have same point values but opposite signs or different teams
                points = [outcome.get("point") for outcome in outcomes]
                if None in points:
                    return False
                # Points should be opposite (e.g., +7.5 and -7.5) or different teams
                return abs(points[0] + points[1]) < 0.1 or points[0] != points[1]

            elif market_key == "totals":
                # Should have same point threshold but "Over" vs "Under"
                points = [outcome.get("point") for outcome in outcomes]
                if None in points or points[0] != points[1]:
                    return False
                # Check for Over/Under naming
                names_lower = outcome_names
                return "over" in names_lower and "under" in names_lower

            return True

        # For player/pitcher/batter props, check for Over/Under pairs by player
        if market_key.startswith(("player_", "pitcher_", "batter_")):
            # Group outcomes by player (description) and check for over/under pairs
            players = {}
            for outcome in outcomes:
                description = outcome.get("description", "").strip()
                name = outcome.get("name", "").strip().lower()
                point = outcome.get("point")

                if not description or not name:
                    continue

                if description not in players:
                    players[description] = {"outcomes": [], "points": set()}

                players[description]["outcomes"].append(name)
                if point is not None:
                    players[description]["points"].add(point)

            # Check that we have at least one player with valid over/under pair
            valid_players = 0
            for player_data in players.values():
                player_outcomes = player_data["outcomes"]
                player_points = player_data["points"]

                # Must have exactly 2 outcomes (over/under) with same point threshold
                if (
                    len(player_outcomes) == 2
                    and len(player_points) == 1
                    and "over" in player_outcomes
                    and "under" in player_outcomes
                ):
                    valid_players += 1

            # Must have at least one valid player with over/under pair
            return valid_players > 0

        # For other markets, check for basic two-outcome structure
        if len(outcomes) == 2:
            # Ensure different outcome names
            outcome_names = [outcome.get("name", "").strip().lower() for outcome in outcomes]
            return len(set(outcome_names)) == 2

        return False

    def get_quota_status(self) -> Dict[str, Any]:
        """Get current API quota status"""
        # Make a minimal request to check quota
        response = self.session.get(
            f"{self.base_url}/sports", params={"apiKey": self.api_key, "all": "false"}
        )

        quota_info = {
            "remaining": response.headers.get("x-requests-remaining", "Unknown"),
            "used": response.headers.get("x-requests-used", "Unknown"),
            "last_cost": response.headers.get("x-requests-last", "Unknown"),
        }

        return quota_info

    def _enrich_event_with_additional_markets(
        self, event: Dict[str, Any], sport_key: str
    ) -> Dict[str, Any]:
        """Enrich an event with additional markets from the event-specific endpoint"""
        additional_markets = ADDITIONAL_MARKETS.get(sport_key, [])
        if not additional_markets:
            return event

        event_id = event.get("id")
        if not event_id:
            return event

        # Get bookmaker keys for our 5 platforms
        bookmaker_keys = [bm["key"] for bm in BOOKMAKERS.values()]

        params = {
            "regions": "us,us_ex,eu",  # Include us_ex for exchanges
            "markets": ",".join(additional_markets),
            "bookmakers": ",".join(bookmaker_keys),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        endpoint = f"sports/{sport_key}/events/{event_id}/odds"
        additional_data = self._make_request(endpoint, params)

        if additional_data and additional_data.get("bookmakers"):
            # Merge additional markets into existing bookmakers
            existing_bookmakers = {bm["key"]: bm for bm in event.get("bookmakers", [])}

            for additional_bm in additional_data.get("bookmakers", []):
                bm_key = additional_bm["key"]
                if bm_key in existing_bookmakers:
                    # Add additional markets to existing bookmaker
                    existing_bookmakers[bm_key]["markets"].extend(additional_bm.get("markets", []))
                else:
                    # Add new bookmaker with additional markets
                    existing_bookmakers[bm_key] = additional_bm

            # Update event with merged bookmaker data
            event["bookmakers"] = list(existing_bookmakers.values())

        return event


def test_api_connection():
    """Test function to verify API connection and quota"""
    try:
        client = OddsAPIClient()

        logger.info("Testing API connection...")
        sports = client.get_active_sports()
        logger.info(f"Successfully connected. Found {len(sports)} active sports.")

        quota = client.get_quota_status()
        logger.info(f"Quota status: {quota}")

        return True

    except Exception as e:
        logger.error(f"API connection failed: {e}")
        return False


if __name__ == "__main__":
    test_api_connection()

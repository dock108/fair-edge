"""
Synchronous Betting Opportunities Persistence Service

Handles saving betting opportunities to the database with proper data normalization,
batch operations, and error handling that doesn't break the refresh pipeline.
Specifically designed for Celery tasks with pgbouncer compatibility.
"""

import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import dateutil.parser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Bet, BetOffer
from services.persistence_monitoring import persistence_monitor
from utils.math_utils import MathUtils

logger = logging.getLogger(__name__)


class SyncBetPersistenceService:
    """Synchronous service for persisting betting opportunities to the database"""

    def __init__(self):
        self.refresh_cycle_id = None

    def save_opportunities_batch(
        self, opportunities: List[Dict[str, Any]], source: str = "refresh_task"
    ) -> Dict[str, Any]:
        """
        Save a batch of betting opportunities to the database synchronously

        Args:
            opportunities: List of opportunity dictionaries from the processing pipeline
            source: Source identifier for this batch (e.g., "refresh_task", "manual")

        Returns:
            Dict with results including counts, errors, and timing
        """
        start_time = datetime.now()
        self.refresh_cycle_id = str(uuid.uuid4())

        results: Dict[str, Any] = {
            "status": "success",
            "refresh_cycle_id": self.refresh_cycle_id,
            "source": source,
            "total_opportunities": len(opportunities),
            "bets_created": 0,
            "bets_updated": 0,
            "offers_created": 0,
            "errors": [],
            "processing_time_ms": 0,
        }

        if not opportunities:
            logger.warning("No opportunities provided to save")
            return results

        # Use Supabase REST API as primary persistence method
        try:
            result = self._save_via_rest_api(opportunities, source, results)

            # Calculate processing time
            end_time = datetime.now()
            result["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

            # Record operation for monitoring
            persistence_monitor.record_batch_operation(result)

            return result

        except Exception as e:
            logger.error(f"REST API persistence failed: {e}", exc_info=True)
            results["status"] = "error"
            results["errors"].append({"type": "api_error", "message": str(e)})

            # Calculate processing time even for failures
            end_time = datetime.now()
            results["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

            return results

    def _extract_bet_data(self, opportunity: Dict[str, Any], bet_id: str) -> Dict[str, Any]:
        """Extract static bet data from opportunity"""
        # Extract teams from event name
        event_name = opportunity.get("Event", "")
        home_team, away_team = self._parse_teams(event_name)

        # Extract player name for props
        player_name = self._extract_player_name(opportunity)

        # Determine sport and league
        sport_id = self._determine_sport(opportunity)
        league_id = self._determine_league(opportunity, sport_id)

        # Extract bet type and description
        bet_type = opportunity.get("Market", "unknown")
        market_description = opportunity.get("Bet Description", "")

        # Parse parameters and outcome side
        parameters, outcome_side = self._parse_bet_parameters(opportunity)

        # Parse event time from opportunity data
        event_time = self._parse_event_time(opportunity)

        # Generate sha_key for event-level deduplication
        sha_key = self._generate_sha_key(event_name, event_time, sport_id)

        return {
            "bet_id": bet_id,
            "sport": sport_id,
            "league": league_id,
            "event_name": event_name,
            "home_team": home_team,
            "away_team": away_team,
            "player_name": player_name,
            "bet_type": bet_type,
            "market_description": market_description,
            "parameters": parameters,
            "outcome_side": outcome_side,
            "event_time": event_time,
            "sha_key": sha_key,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def _extract_offer_data(self, opportunity: Dict[str, Any], bet_id: str) -> Dict[str, Any]:
        """Extract offer data from opportunity"""
        # Parse odds data
        odds_data = self._parse_odds_data(opportunity)

        # Calculate fair odds
        fair_odds_data = self._parse_fair_odds(opportunity)

        # Determine book/source
        book_id = self._determine_book(opportunity)

        # Extract EV and confidence metrics
        expected_value = opportunity.get("EV_Raw", 0.0)
        confidence_score = self._calculate_confidence_score(opportunity)

        return {
            "offer_id": BetOffer.generate_offer_id(),
            "bet_id": bet_id,
            "book": book_id,
            "odds": odds_data,
            "expected_value": expected_value,
            "fair_odds": fair_odds_data,
            "implied_probability": self._calculate_implied_probability(odds_data),
            "confidence_score": confidence_score,
            "volume_indicator": self._determine_volume_indicator(opportunity),
            "available_limits": self._extract_limits(opportunity),
            "offer_metadata": self._extract_offer_metadata(opportunity),
            "timestamp": datetime.now(),
            "refresh_cycle_id": self.refresh_cycle_id,
        }

    # All the parsing and extraction methods remain the same as the async version
    def _parse_teams(self, event_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse team names from event string with improved cleaning"""
        if not event_name:
            return None, None

        # Clean up the event name - remove time/date info
        clean_event = event_name

        # Remove common date/time patterns
        import re

        time_patterns = [
            r"\s*•\s*Today\s+\d{1,2}:\d{2}[AP]M\s+EST",
            r"\s*•\s*Tomorrow\s+\d{1,2}:\d{2}[AP]M\s+EST",
            r"\s*•\s*\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}[AP]M\s+EST",
            r"\s*•.*$",  # Remove everything after bullet point
        ]

        for pattern in time_patterns:
            clean_event = re.sub(pattern, "", clean_event, flags=re.IGNORECASE)

        clean_event = clean_event.strip()

        # Parse teams from cleaned event name
        if " vs " in clean_event:
            parts = clean_event.split(" vs ")
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        elif " @ " in clean_event:
            parts = clean_event.split(" @ ")
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()  # home @ away

        return None, None

    def _extract_player_name(self, opportunity: Dict[str, Any]) -> Optional[str]:
        """Extract player name for prop bets with improved parsing"""
        description = opportunity.get("Bet Description", "")
        if not description:
            return None

        # Baseball prop keywords
        baseball_prop_keywords = [
            "hits",
            "strikeouts",
            "earned runs",
            "total bases",
            "hits allowed",
            "runs",
            "rbi",
            "home runs",
            "walks",
            "innings pitched",
            "outs",
        ]

        # Check if this is a baseball prop bet
        description_lower = description.lower()
        if any(keyword in description_lower for keyword in baseball_prop_keywords):
            # For baseball props, player name is typically at the beginning
            # Examples: "Zac Gallen Over 2.5 Earned Runs", "Ketel Marte Under 1.5 Total Bases"
            import re

            # Extract name before "Over/Under" or before prop keyword
            over_under_match = re.match(r"^(.+?)\s+(Over|Under)\s+", description, re.IGNORECASE)
            if over_under_match:
                potential_name = over_under_match.group(1).strip()
                # Clean up any remaining artifacts
                potential_name = re.sub(r"\s+", " ", potential_name)
                return potential_name if len(potential_name.split()) <= 3 else None

            # Fallback: extract first 1-3 words if they don't contain prop keywords
            words = description.split()
            if len(words) >= 2:
                for i in range(min(3, len(words)), 0, -1):
                    potential_name = " ".join(words[:i])
                    if not any(
                        keyword in potential_name.lower() for keyword in baseball_prop_keywords
                    ):
                        return potential_name

        return None

    def _determine_sport(self, opportunity: Dict[str, Any]) -> str:
        """Determine sport ID from opportunity data"""
        description = opportunity.get("Bet Description", "").lower()
        event = opportunity.get("Event", "").lower()

        # MLB/Baseball patterns - check for team names and baseball-specific terms
        baseball_teams = [
            "giants",
            "diamondbacks",
            "dodgers",
            "white sox",
            "mariners",
            "royals",
            "athletics",
            "rays",
            "angels",
            "braves",
            "astros",
            "rockies",
            "yankees",
            "blue jays",
            "cubs",
            "cardinals",
            "brewers",
            "twins",
            "tigers",
            "guardians",
            "orioles",
            "red sox",
            "mets",
            "phillies",
            "nationals",
            "marlins",
            "pirates",
            "reds",
            "padres",
            "rangers",
        ]

        baseball_terms = [
            "mlb",
            "baseball",
            "hits",
            "strikeouts",
            "earned runs",
            "total bases",
            "hits allowed",
            "pitcher",
            "batter",
            "innings",
            "runs",
            "rbi",
            "home runs",
        ]

        # Check for MLB team names or baseball-specific terms
        if any(team in event for team in baseball_teams) or any(
            term in description or term in event for term in baseball_terms
        ):
            return "baseball_mlb"

        # NFL/Football patterns
        if any(
            term in description or term in event
            for term in ["nfl", "football", "touchdown", "yards"]
        ):
            return "americanfootball_nfl"

        # NBA/Basketball patterns
        if any(
            term in description or term in event
            for term in ["nba", "basketball", "points", "rebounds"]
        ):
            return "basketball_nba"

        # NHL/Hockey patterns
        if any(
            term in description or term in event for term in ["nhl", "hockey", "goals", "shots"]
        ):
            return "icehockey_nhl"

        # Default fallback
        return "unknown"

    def _determine_league(self, opportunity: Dict[str, Any], sport_id: str) -> str:
        """Determine league ID based on sport"""
        # Simple mapping of sport to primary league
        sport_to_league = {
            "americanfootball_nfl": "nfl",
            "basketball_nba": "nba",
            "baseball_mlb": "mlb",
            "icehockey_nhl": "nhl",
        }
        return sport_to_league.get(sport_id, "unknown")

    def _parse_bet_parameters(
        self, opportunity: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Parse bet parameters and outcome side from description"""
        description = opportunity.get("Bet Description", "").lower()
        parameters = {}
        outcome_side = None

        # Parse spread values
        import re

        spread_match = re.search(r"[+-]?\d+\.?\d*", description)
        if "spread" in description and spread_match:
            parameters["spread"] = float(spread_match.group())

        # Parse total values
        total_match = re.search(r"\d+\.?\d*", description)
        if any(term in description for term in ["total", "over", "under"]) and total_match:
            parameters["total"] = float(total_match.group())

        # Determine outcome side
        if "over" in description:
            outcome_side = "over"
        elif "under" in description:
            outcome_side = "under"
        elif "home" in description:
            outcome_side = "home"
        elif "away" in description:
            outcome_side = "away"

        return parameters, outcome_side

    def _parse_event_time(self, opportunity: Dict[str, Any]) -> Optional[datetime]:
        """Parse event start time from opportunity data with robust timezone handling"""
        # Check common field names for event time
        time_fields = ["commence_time", "event_time", "start_time", "game_time"]

        for field in time_fields:
            time_value = opportunity.get(field)
            if not time_value:
                continue

            try:
                # Handle Unix timestamp (seconds or milliseconds)
                if isinstance(time_value, (int, float)):
                    # Check if it's in milliseconds (typical for JavaScript timestamps)
                    if time_value > 1e12:  # Likely milliseconds
                        timestamp = time_value / 1000
                    else:  # Likely seconds
                        timestamp = time_value

                    # Convert to UTC datetime
                    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

                # Handle string timestamps (ISO format)
                elif isinstance(time_value, str):
                    # Parse ISO format string with timezone awareness
                    parsed_time = dateutil.parser.parse(time_value)

                    # Ensure timezone-aware (default to UTC if naive)
                    if parsed_time.tzinfo is None:
                        parsed_time = parsed_time.replace(tzinfo=timezone.utc)

                    # Convert to UTC for consistent storage
                    return parsed_time.astimezone(timezone.utc)

            except (ValueError, TypeError, OverflowError) as e:
                logger.warning(
                    f"Failed to parse time field '{field}' with value '{time_value}': {e}"
                )
                continue

        # If no valid time found, log a warning and return None
        logger.debug(
            f"No valid event time found in opportunity: {opportunity.get('Event', 'unknown')}"
        )
        return None

    def _generate_sha_key(
        self, event_name: str, event_time: Optional[datetime], sport_id: str
    ) -> str:
        """Generate SHA key for event-level deduplication"""
        # Create a hash input that groups bets from the same event
        # Use event name, time, and sport to create unique event identifier
        hash_components = [
            str(event_name or ""),
            str(event_time.isoformat() if event_time else ""),
            str(sport_id or ""),
        ]

        hash_input = "|".join(hash_components)

        # Generate SHA-256 hash and return first 16 characters for shorter key
        full_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        return full_hash[:16]

    def _parse_odds_data(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse odds data into structured format with improved error handling"""
        best_odds = opportunity.get("Best Available Odds", "+100")

        try:
            # Clean up the odds string - extract just the numeric part
            import re

            # Handle formats like "ProphetX 184 (180)", "+150", "-110", etc.
            # Extract the first number that looks like odds
            odds_match = re.search(r"[+-]?\d+", str(best_odds))

            if odds_match:
                odds_str = odds_match.group()
                # Ensure it has a sign
                if not odds_str.startswith(("+", "-")):
                    odds_str = "+" + odds_str
            else:
                # Fallback to even odds
                odds_str = "+100"

            # Convert American odds to decimal
            if odds_str.startswith("-"):
                american_int = -int(odds_str[1:])
            else:
                american_int = int(odds_str.replace("+", ""))

            decimal_odds = MathUtils.american_to_decimal(american_int)

            return {
                "american": odds_str,
                "decimal": decimal_odds,
                "source": opportunity.get("Best_Odds_Source", "unknown"),
                "raw": str(best_odds),  # Keep original for debugging
            }

        except Exception as e:
            # Fallback to even odds if parsing fails
            logger.warning(f"Failed to parse odds '{best_odds}': {e}")
            return {
                "american": "+100",
                "decimal": 2.0,
                "source": opportunity.get("Best_Odds_Source", "unknown"),
                "raw": str(best_odds),
                "parse_error": str(e),
            }

    def _parse_fair_odds(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fair odds data with improved error handling"""
        fair_odds = opportunity.get("Fair Odds", "+100")

        try:
            # Clean up the odds string - extract just the numeric part
            import re

            # Handle formats like "ProphetX 184 (180)", "+150", "-110", etc.
            odds_match = re.search(r"[+-]?\d+", str(fair_odds))

            if odds_match:
                odds_str = odds_match.group()
                # Ensure it has a sign
                if not odds_str.startswith(("+", "-")):
                    odds_str = "+" + odds_str
            else:
                # Fallback to even odds
                odds_str = "+100"

            # Convert American odds to decimal
            if odds_str.startswith("-"):
                american_int = -int(odds_str[1:])
            else:
                american_int = int(odds_str.replace("+", ""))

            decimal_odds = MathUtils.american_to_decimal(american_int)

            return {
                "american": odds_str,
                "decimal": decimal_odds,
                "raw": str(fair_odds),
            }

        except Exception as e:
            # Fallback to even odds if parsing fails
            logger.warning(f"Failed to parse fair odds '{fair_odds}': {e}")
            return {
                "american": "+100",
                "decimal": 2.0,
                "raw": str(fair_odds),
                "parse_error": str(e),
            }

    def _determine_book(self, opportunity: Dict[str, Any]) -> Optional[str]:
        """Determine bookmaker ID from opportunity, returns None if not a supported book"""
        source = opportunity.get("Best_Odds_Source", "")

        # Only support these 5 books
        known_books = {"novig", "prophetx", "draftkings", "fanduel", "pinnacle"}

        # Normalize common bookmaker names with comprehensive matching
        book_mapping = {
            "draftkings": "draftkings",
            "fanduel": "fanduel",
            "novig": "novig",
            "pinnacle": "pinnacle",
            "prophetx": "prophetx",
            "prophet x": "prophetx",
            "prophet_x": "prophetx",
        }

        source_lower = source.lower().strip()

        # Check direct mapping first
        for key, value in book_mapping.items():
            if key in source_lower:
                return value

        # Try partial matches for variations
        if "draft" in source_lower and "king" in source_lower:
            return "draftkings"
        if "fan" in source_lower and "duel" in source_lower:
            return "fanduel"
        if "prophet" in source_lower:
            return "prophetx"
        if "pinnacle" in source_lower:
            return "pinnacle"
        if "novig" in source_lower or "no vig" in source_lower:
            return "novig"

        # If not found, return None to indicate we should skip this opportunity
        logger.debug(f"Unsupported book source '{source}', skipping opportunity")
        return None

    def _calculate_implied_probability(self, odds_data: Dict[str, Any]) -> float:
        """Calculate implied probability from decimal odds"""
        try:
            decimal_odds = odds_data.get("decimal", 2.0)
            return 1 / decimal_odds if decimal_odds > 0 else 0.5
        except (ZeroDivisionError, TypeError):
            return 0.5

    def _calculate_confidence_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate confidence score for this opportunity"""
        # Simple confidence calculation based on EV and other factors
        ev_raw = opportunity.get("EV_Raw", 0.0)

        # Higher EV = higher confidence, capped at 1.0
        base_confidence = min(abs(ev_raw) * 10, 1.0)

        # Adjust based on data completeness
        if opportunity.get("All Available Odds", "N/A") != "N/A":
            base_confidence *= 1.1  # Boost for complete odds data

        return min(base_confidence, 1.0)

    def _determine_volume_indicator(self, opportunity: Dict[str, Any]) -> str:
        """Determine volume indicator for the market"""
        # Simple heuristic based on available information
        odds_count = len(opportunity.get("All Available Odds", "").split(";"))

        if odds_count >= 5:
            return "high"
        elif odds_count >= 3:
            return "medium"
        else:
            return "low"

    def _extract_limits(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract betting limits if available"""
        # This would be enhanced when limit data is available
        return None

    def _extract_offer_metadata(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional offer metadata"""
        return {
            "links": opportunity.get("Links", ""),
            "all_odds": opportunity.get("All Available Odds", ""),
            "processing_notes": opportunity.get("processing_notes", ""),
        }

    def _save_via_rest_api(
        self, opportunities: List[Dict[str, Any]], source: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Primary persistence implementation using Supabase REST API
        """
        try:
            logger.info("Saving opportunities via Supabase REST API")
            import os

            import requests

            # Get Supabase credentials
            supabase_url = os.getenv("SUPABASE_URL")
            service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not supabase_url or not service_key:
                logger.error("Supabase credentials not available")
                results["status"] = "error"
                results["errors"].append(
                    {"type": "config_error", "message": "Supabase credentials missing"}
                )
                return results

            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",  # Don't return data, just status
            }

            # First, ensure lookup data exists
            self._ensure_lookup_data_via_api(supabase_url, headers)

            # Process opportunities in batches
            batch_size = 50  # Optimal batch size for REST API
            bets_created = 0
            bets_updated = 0
            offers_created = 0
            offers_skipped = 0
            filtered_out = 0

            for i in range(0, len(opportunities), batch_size):
                batch = opportunities[i : i + batch_size]
                batch_results = self._process_api_batch(batch, supabase_url, headers)

                bets_created += batch_results["bets_created"]
                bets_updated += batch_results["bets_updated"]
                offers_created += batch_results["offers_created"]
                offers_skipped += batch_results.get("offers_skipped", 0)
                filtered_out += batch_results.get("filtered_out", 0)
                results["errors"].extend(batch_results["errors"])

            logger.info(
                f"✅ REST API persistence completed: {bets_created} bets created, {offers_created} offers created, {offers_skipped} offers skipped (duplicates)"
            )

            # Update results
            results["status"] = "success"
            results["bets_created"] = bets_created
            results["bets_updated"] = bets_updated
            results["offers_created"] = offers_created
            results["offers_skipped"] = offers_skipped
            results["filtered_out"] = filtered_out

            return results

        except Exception as e:
            logger.error(f"REST API persistence failed: {e}")
            results["status"] = "error"
            results["errors"].append({"type": "api_error", "message": str(e)})
            return results

    def _ensure_lookup_data_via_api(self, supabase_url: str, headers: Dict[str, str]):
        """Ensure lookup data exists via REST API"""
        import requests

        # Sports data
        sports_data = [
            {
                "sport_id": "americanfootball_nfl",
                "name": "NFL",
                "category": "americanfootball",
            },
            {"sport_id": "basketball_nba", "name": "NBA", "category": "basketball"},
            {"sport_id": "baseball_mlb", "name": "MLB", "category": "baseball"},
            {"sport_id": "icehockey_nhl", "name": "NHL", "category": "icehockey"},
            {"sport_id": "unknown", "name": "Unknown Sport", "category": "unknown"},
        ]

        # Leagues data
        leagues_data = [
            {
                "league_id": "nfl",
                "name": "National Football League",
                "sport_id": "americanfootball_nfl",
            },
            {
                "league_id": "nba",
                "name": "National Basketball Association",
                "sport_id": "basketball_nba",
            },
            {
                "league_id": "mlb",
                "name": "Major League Baseball",
                "sport_id": "baseball_mlb",
            },
            {
                "league_id": "nhl",
                "name": "National Hockey League",
                "sport_id": "icehockey_nhl",
            },
            {"league_id": "unknown", "name": "Unknown League", "sport_id": "unknown"},
        ]

        # Books data - only the 5 supported books
        books_data = [
            {
                "book_id": "draftkings",
                "name": "DraftKings",
                "book_type": "us_book",
                "region": "us",
            },
            {
                "book_id": "fanduel",
                "name": "FanDuel",
                "book_type": "us_book",
                "region": "us",
            },
            {
                "book_id": "novig",
                "name": "NoVig",
                "book_type": "us_book",
                "region": "us",
            },
            {
                "book_id": "prophetx",
                "name": "ProphetX",
                "book_type": "us_book",
                "region": "us",
            },
            {
                "book_id": "pinnacle",
                "name": "Pinnacle",
                "book_type": "sharp",
                "region": "global",
            },
        ]

        # Insert lookup data with ON CONFLICT handling
        for table, data in [
            ("sports", sports_data),
            ("leagues", leagues_data),
            ("books", books_data),
        ]:
            try:
                response = requests.post(
                    f"{supabase_url}/rest/v1/{table}",
                    headers={**headers, "Prefer": "resolution=ignore-duplicates"},
                    json=data,
                    timeout=30,
                )
                if response.status_code not in [200, 201]:
                    logger.warning(
                        f"Failed to upsert {table}: {response.status_code} {response.text}"
                    )
            except Exception as e:
                logger.warning(f"Error upserting {table}: {e}")

    def _process_api_batch(
        self,
        opportunities: List[Dict[str, Any]],
        supabase_url: str,
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Process a batch of opportunities via REST API with aggregation by bet_id"""
        import requests

        batch_results: Dict[str, Any] = {
            "bets_created": 0,
            "bets_updated": 0,
            "offers_created": 0,
            "offers_skipped": 0,
            "filtered_out": 0,
            "errors": [],
        }

        # Group opportunities by bet_id and extract all books from "All Available Odds"
        bet_groups: Dict[str, Dict[str, Any]] = {}

        for opportunity in opportunities:
            try:
                # Extract bet data
                bet_id = Bet.create_or_get_bet_id(opportunity)

                # Create bet group if it doesn't exist
                if bet_id not in bet_groups:
                    bet_groups[bet_id] = {
                        "bet_data": self._extract_bet_data(opportunity, bet_id),
                        "books": {},
                        "opportunity": opportunity,  # Store the full opportunity for later use
                    }
                    logger.debug(
                        f"Created new bet group: {bet_id[:16]}... for {opportunity.get('Event', 'Unknown')[:50]}..."
                    )

                # For now, still use the single book method but store the opportunity
                # The key change is in _create_aggregated_offer where we'll parse "All Available Odds"
                book_id = self._determine_book(opportunity)
                if book_id:
                    odds_data = self._parse_odds_data(opportunity)
                    expected_value = opportunity.get("EV_Raw", 0.0)

                    bet_groups[bet_id]["books"][book_id] = {
                        "odds": odds_data,
                        "expected_value": expected_value,
                        "opportunity": opportunity,
                    }
                    logger.debug(f"Added {book_id} to bet group: {bet_id[:16]}...")
                else:
                    batch_results["filtered_out"] += 1

            except Exception as e:
                batch_results["errors"].append(
                    {
                        "type": "extraction_error",
                        "message": str(e),
                        "opportunity": opportunity.get("Event", "unknown"),
                    }
                )

        # Now create aggregated bet and offer records
        bet_records = []
        offer_records = []

        logger.info(
            f"📊 Aggregation summary: {len(bet_groups)} unique bets from {len(opportunities)} opportunities"
        )

        # Log some examples of aggregation
        for i, (bet_id, group_data) in enumerate(bet_groups.items()):
            if i < 3:  # Log first 3 examples
                books_list = list(group_data["books"].keys())
                logger.info(
                    f"  Bet {i+1}: {bet_id[:16]}... has {len(books_list)} books: {books_list}"
                )

        for bet_id, group_data in bet_groups.items():
            try:
                # Prepare bet record
                bet_data: Dict[str, Any] = group_data["bet_data"]

                # Convert datetime to ISO string for API
                if bet_data.get("event_time"):
                    bet_data["event_time"] = bet_data["event_time"].isoformat()
                if bet_data.get("created_at"):
                    bet_data["created_at"] = bet_data["created_at"].isoformat()
                if bet_data.get("updated_at"):
                    bet_data["updated_at"] = bet_data["updated_at"].isoformat()

                bet_records.append(bet_data)

                # Create aggregated offer data
                offer_data: Dict[str, Any] = self._create_aggregated_offer(
                    bet_id, group_data["books"]
                )

                # For batch processing, always create the aggregated offer
                # The database will handle any constraint conflicts
                # Convert datetime to ISO string for API
                if offer_data.get("timestamp"):
                    offer_data["timestamp"] = offer_data["timestamp"].isoformat()

                offer_records.append(offer_data)
                logger.debug(
                    f"Created aggregated offer for bet {bet_id} with {len(group_data['books'])} books"
                )

            except Exception as e:
                batch_results["errors"].append(
                    {"type": "aggregation_error", "message": str(e), "bet_id": bet_id}
                )

        # Insert bets with conflict resolution
        if bet_records:
            try:
                response = requests.post(
                    f"{supabase_url}/rest/v1/bets",
                    headers={**headers, "Prefer": "resolution=ignore-duplicates"},
                    json=bet_records,
                    timeout=60,
                )
                if response.status_code in [200, 201]:
                    batch_results["bets_created"] = len(bet_records)
                else:
                    logger.warning(f"Bets insert failed: {response.status_code} {response.text}")
                    batch_results["errors"].append(
                        {
                            "type": "bets_insert_error",
                            "message": f"HTTP {response.status_code}: {response.text}",
                        }
                    )
            except Exception as e:
                batch_results["errors"].append({"type": "bets_api_error", "message": str(e)})

        # Insert offers (always new records)
        if offer_records:
            try:
                response = requests.post(
                    f"{supabase_url}/rest/v1/bet_offers",
                    headers=headers,
                    json=offer_records,
                    timeout=60,
                )
                if response.status_code in [200, 201]:
                    batch_results["offers_created"] = len(offer_records)
                else:
                    logger.warning(f"Offers insert failed: {response.status_code} {response.text}")
                    batch_results["errors"].append(
                        {
                            "type": "offers_insert_error",
                            "message": f"HTTP {response.status_code}: {response.text}",
                        }
                    )
            except Exception as e:
                batch_results["errors"].append({"type": "offers_api_error", "message": str(e)})

        return batch_results

    def _parse_all_available_odds(self, opportunity: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Parse the 'All Available Odds' field to extract individual book data"""
        all_odds_str = opportunity.get("All Available Odds", "")
        if not all_odds_str or all_odds_str == "N/A":
            return {}

        books_data = {}

        # Parse format: "DraftKings: +120; FanDuel: +124; Pinnacle: +125; ProphetX: +142 (+139); Novig: +155 (+152)"
        odds_parts = all_odds_str.split(";")

        for part in odds_parts:
            part = part.strip()
            if ":" in part:
                try:
                    book_display, odds_str = part.split(":", 1)
                    book_display = book_display.strip()
                    odds_str = odds_str.strip()

                    # Map display names to book IDs
                    book_mapping = {
                        "draftkings": "draftkings",
                        "fanduel": "fanduel",
                        "novig": "novig",
                        "pinnacle": "pinnacle",
                        "prophetx": "prophetx",
                    }

                    book_id = None
                    for key, value in book_mapping.items():
                        if key in book_display.lower():
                            book_id = value
                            break

                    if book_id:
                        # Extract American odds (handle both "+120" and "+142 (+139)" formats)
                        import re

                        odds_match = re.search(r"([+-]?\d+)", odds_str)
                        if odds_match:
                            american_odds = odds_match.group(1)
                            if not american_odds.startswith(("+", "-")):
                                american_odds = "+" + american_odds

                            # Convert to decimal
                            american_int = (
                                int(american_odds.replace("+", ""))
                                if american_odds.startswith("+")
                                else int(american_odds)
                            )
                            decimal_odds = MathUtils.american_to_decimal(american_int)

                            books_data[book_id] = {
                                "american": american_odds,
                                "decimal": decimal_odds,
                                "source": book_id,
                                "raw": odds_str,
                            }

                except Exception as e:
                    logger.debug(f"Failed to parse odds part '{part}': {e}")
                    continue

        return books_data

    def _create_aggregated_offer(self, bet_id: str, books_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create aggregated offer data from multiple books"""
        from datetime import datetime

        # Get the opportunity data to extract "All Available Odds"
        opportunity = None
        if books_data:
            first_book = list(books_data.keys())[0]
            opportunity = books_data[first_book].get("opportunity")

        # Initialize the aggregated offer structure
        offer_data = {
            "offer_id": BetOffer.generate_offer_id(),
            "bet_id": bet_id,
            "timestamp": datetime.now(),
            "refresh_cycle_id": self.refresh_cycle_id,
            "books_count": len(books_data),
        }

        # Parse "All Available Odds" to get all book data
        all_books_odds = {}
        if opportunity:
            all_books_odds = self._parse_all_available_odds(opportunity)

        # Set individual book odds (None if book not available)
        supported_books = ["draftkings", "fanduel", "novig", "prophetx", "pinnacle"]
        books_found = 0

        for book in supported_books:
            book_key = f"{book}_odds"

            if book in all_books_odds:
                # Use parsed data from "All Available Odds"
                book_odds = all_books_odds[book]
                offer_data[book_key] = {
                    "american": book_odds["american"],
                    "decimal": book_odds["decimal"],
                    "source": book_odds["source"],
                    "raw": book_odds["raw"],
                    "expected_value": 0.0,  # Will use the overall EV from opportunity
                }
                books_found += 1
            elif book in books_data:
                # Fallback to original method
                book_info = books_data[book]
                offer_data[book_key] = {
                    **book_info["odds"],
                    "expected_value": book_info.get("expected_value", 0.0),
                }
                books_found += 1
            else:
                offer_data[book_key] = None

        # Update books_count to reflect actual books found
        offer_data["books_count"] = books_found

        # Calculate aggregated metrics
        available_books = list(books_data.keys())
        evs = [books_data[book]["expected_value"] for book in available_books]

        # Find best EV and corresponding book
        if evs:
            best_ev_idx = evs.index(max(evs))
            best_book = available_books[best_ev_idx]
            offer_data["best_expected_value"] = max(evs)
            offer_data["best_book"] = best_book
            offer_data["best_odds"] = books_data[best_book]["odds"]
        else:
            offer_data["best_expected_value"] = 0.0
            offer_data["best_book"] = None
            offer_data["best_odds"] = None

        # Calculate fair odds (use first available opportunity)
        if available_books:
            first_book = available_books[0]
            first_opportunity = books_data[first_book]["opportunity"]
            offer_data["fair_odds"] = self._parse_fair_odds(first_opportunity)
        else:
            offer_data["fair_odds"] = None

        # Calculate market average (simple average of decimal odds)
        if len(available_books) > 1:
            decimal_odds = []
            for book in available_books:
                decimal = books_data[book]["odds"].get("decimal", 0)
                if decimal > 0:
                    decimal_odds.append(decimal)

            if decimal_odds:
                avg_decimal = sum(decimal_odds) / len(decimal_odds)
                # Convert back to American odds for consistency
                if avg_decimal >= 2.0:
                    avg_american = f"+{int((avg_decimal - 1) * 100)}"
                else:
                    avg_american = f"-{int(100 / (avg_decimal - 1))}"

                offer_data["market_average"] = {
                    "american": avg_american,
                    "decimal": avg_decimal,
                }
            else:
                offer_data["market_average"] = None
        else:
            offer_data["market_average"] = None

        # Set confidence and volume metrics (use best book's data)
        if available_books:
            best_opportunity = books_data[best_book]["opportunity"]
            offer_data["confidence_score"] = self._calculate_confidence_score(best_opportunity)
            offer_data["volume_indicator"] = self._determine_volume_indicator(best_opportunity)
        else:
            offer_data["confidence_score"] = 0.0
            offer_data["volume_indicator"] = "low"

        # Metadata
        offer_data["offer_metadata"] = {
            "books_available": available_books,
            "aggregation_method": "best_ev",
            "refresh_cycle_id": self.refresh_cycle_id,
        }

        return offer_data

    def _should_create_new_aggregated_offer(
        self,
        bet_id: str,
        new_offer_data: Dict[str, Any],
        supabase_url: str,
        headers: Dict[str, str],
    ) -> bool:
        """Check if we should create a new aggregated offer"""
        import requests

        try:
            # Get the most recent offer for this bet
            response = requests.get(
                f"{supabase_url}/rest/v1/bet_offers",
                headers=headers,
                params={
                    "bet_id": f"eq.{bet_id}",
                    "order": "timestamp.desc",
                    "limit": "1",
                },
                timeout=10,
            )

            if response.status_code != 200:
                logger.warning(
                    f"Failed to fetch existing offers for bet {bet_id}: {response.status_code}"
                )
                return True

            existing_offers = response.json()
            if not existing_offers:
                return True

            latest_offer = existing_offers[0]

            # Compare aggregated fields
            comparison_fields = [
                "best_expected_value",
                "best_book",
                "books_count",
                "draftkings_odds",
                "fanduel_odds",
                "novig_odds",
                "prophetx_odds",
                "pinnacle_odds",
            ]

            for field in comparison_fields:
                old_value = latest_offer.get(field)
                new_value = new_offer_data.get(field)

                # Handle book odds comparison (nested JSON)
                if field.endswith("_odds"):
                    if self._odds_significantly_different(old_value, new_value):
                        logger.debug(f"Aggregated offer change detected in {field}")
                        return True
                elif field == "best_expected_value":
                    # Use same 0.01 threshold as before
                    old_ev = float(old_value or 0)
                    new_ev = float(new_value or 0)
                    if abs(old_ev - new_ev) >= 0.01:
                        logger.debug(f"Significant EV change: {old_ev} -> {new_ev}")
                        return True
                elif old_value != new_value:
                    logger.debug(
                        f"Aggregated offer change detected in {field}: {old_value} -> {new_value}"
                    )
                    return True

            # No meaningful changes detected
            return False

        except Exception as e:
            logger.warning(f"Error checking for duplicate aggregated offers: {e}")
            return True

    def _odds_significantly_different(self, old_odds: Dict, new_odds: Dict) -> bool:
        """Compare two odds objects for significant differences"""
        # If one is None and other isn't, that's a significant change
        if (old_odds is None) != (new_odds is None):
            return True

        # If both are None, no change
        if old_odds is None and new_odds is None:
            return False

        # Compare key fields
        for field in ["american", "decimal", "expected_value"]:
            old_val = old_odds.get(field) if old_odds else None
            new_val = new_odds.get(field) if new_odds else None

            if field == "expected_value":
                # Use EV threshold
                old_ev = float(old_val or 0)
                new_ev = float(new_val or 0)
                if abs(old_ev - new_ev) >= 0.01:
                    return True
            elif old_val != new_val:
                return True

        return False

    def _should_create_new_offer(
        self,
        bet_id: str,
        new_offer_data: Dict[str, Any],
        supabase_url: str,
        headers: Dict[str, str],
    ) -> bool:
        """Check if we should create a new offer or if it's a duplicate"""
        import requests

        try:
            # Get the most recent offer for this bet
            response = requests.get(
                f"{supabase_url}/rest/v1/bet_offers",
                headers=headers,
                params={
                    "bet_id": f"eq.{bet_id}",
                    "order": "timestamp.desc",
                    "limit": "1",
                },
                timeout=10,
            )

            if response.status_code != 200:
                # If we can't fetch existing offers, create the new one to be safe
                logger.warning(
                    f"Failed to fetch existing offers for bet {bet_id}: {response.status_code}"
                )
                return True

            existing_offers = response.json()
            if not existing_offers:
                # No existing offers, create the new one
                return True

            latest_offer = existing_offers[0]

            # Compare meaningful fields (excluding timestamp and offer_id)
            fields_to_compare = [
                "book",
                "odds",
                "expected_value",
                "fair_odds",
                "implied_probability",
                "confidence_score",
                "volume_indicator",
            ]

            for field in fields_to_compare:
                old_value = latest_offer.get(field)
                new_value = new_offer_data.get(field)

                # Handle nested dict comparison for odds
                if (
                    field in ["odds", "fair_odds"]
                    and isinstance(old_value, dict)
                    and isinstance(new_value, dict)
                ):
                    # Compare key fields in odds objects
                    for odds_field in ["american", "decimal"]:
                        if old_value.get(odds_field) != new_value.get(odds_field):
                            logger.debug(
                                f"Offer change detected in {field}.{odds_field}: {old_value.get(odds_field)} -> {new_value.get(odds_field)}"
                            )
                            return True
                elif old_value != new_value:
                    logger.debug(f"Offer change detected in {field}: {old_value} -> {new_value}")
                    return True

            # Check for significant changes in expected value (threshold: 0.01)
            old_ev = float(latest_offer.get("expected_value", 0))
            new_ev = float(new_offer_data.get("expected_value", 0))
            if abs(old_ev - new_ev) >= 0.01:
                logger.debug(f"Significant EV change detected: {old_ev} -> {new_ev}")
                return True

            # No meaningful changes detected
            return False

        except Exception as e:
            logger.warning(f"Error checking for duplicate offers: {e}")
            # If there's an error, create the offer to be safe
            return True


# Global instance for easy access
sync_bet_persistence = SyncBetPersistenceService()

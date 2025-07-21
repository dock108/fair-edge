"""
Betting Opportunities Persistence Service

Handles saving betting opportunities to the database with proper data normalization,
batch operations, and error handling that doesn't break the refresh pipeline.
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
from sqlalchemy import exists, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import AsyncSessionLocal, get_pgbouncer_session
from models import Bet, BetOffer
from utils.math_utils import MathUtils

logger = logging.getLogger(__name__)


class BetPersistenceService:
    """Service for persisting betting opportunities to the database"""

    def __init__(self):
        self.refresh_cycle_id = None

    async def save_opportunities_batch(
        self, opportunities: List[Dict[str, Any]], source: str = "refresh_task"
    ) -> Dict[str, Any]:
        """
        Save a batch of betting opportunities to the database

        Args:
            opportunities: List of opportunity dictionaries from the processing pipeline
            source: Source identifier for this batch (e.g., "refresh_task", "manual")

        Returns:
            Dict with results including counts, errors, and timing
        """
        start_time = datetime.now()
        self.refresh_cycle_id = str(uuid.uuid4())

        results = {
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

        try:
            if not AsyncSessionLocal:
                raise RuntimeError("Database not configured properly")

            async with get_pgbouncer_session() as session:
                # Ensure lookup data exists
                await self._ensure_lookup_data(session)

                # Process opportunities in batches
                batch_size = 100  # Configurable batch size
                for i in range(0, len(opportunities), batch_size):
                    batch = opportunities[i : i + batch_size]
                    batch_results = await self._process_opportunity_batch(session, batch)

                    # Aggregate results
                    results["bets_created"] += batch_results["bets_created"]
                    results["bets_updated"] += batch_results["bets_updated"]
                    results["offers_created"] += batch_results["offers_created"]
                    results["errors"].extend(batch_results["errors"])

                # Note: Commit handled by pgbouncer session context manager
                logger.info(
                    f"Successfully saved batch: {results['bets_created']} bets, "
                    f"{results['offers_created']} offers"
                )

        except Exception as e:
            logger.error(f"Critical error in batch save: {e}", exc_info=True)
            results["status"] = "error"
            results["errors"].append({"type": "critical", "message": str(e)})

            # Try to rollback the transaction if it's still active
            try:
                if session:
                    await session.rollback()
            except Exception as rollback_error:
                logger.warning(f"Failed to rollback transaction: {rollback_error}")

        # Calculate processing time
        end_time = datetime.now()
        results["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

        return results

    async def _process_opportunity_batch(
        self, session: AsyncSession, opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a single batch of opportunities"""
        results = {
            "bets_created": 0,
            "bets_updated": 0,
            "offers_created": 0,
            "errors": [],
        }

        for opportunity in opportunities:
            try:
                # Extract or create bet record
                bet_result = await self._ensure_bet_record(session, opportunity)
                if bet_result["created"]:
                    results["bets_created"] += 1
                else:
                    results["bets_updated"] += 1

                # Create offer record
                offer_result = await self._create_offer_record(
                    session, bet_result["bet_id"], opportunity
                )
                if offer_result["created"]:
                    results["offers_created"] += 1

            except Exception as e:
                error_msg = f"Error processing opportunity: {str(e)}"
                logger.warning(error_msg)
                results["errors"].append(
                    {
                        "type": "opportunity_error",
                        "message": error_msg,
                        "opportunity_event": opportunity.get("Event", "unknown"),
                    }
                )
                # Continue processing other opportunities
                continue

        return results

    async def _ensure_bet_record(
        self, session: AsyncSession, opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure bet record exists, create if not found"""
        # Generate deterministic bet_id
        bet_id = Bet.create_or_get_bet_id(opportunity)

        # Check if bet already exists using raw SQL for pgbouncer compatibility
        result = await session.execute(
            text("SELECT EXISTS(SELECT 1 FROM bets WHERE bet_id = :bet_id)"),
            {"bet_id": bet_id},
        )
        bet_exists = result.scalar()

        if not bet_exists:
            # Create new bet record using raw SQL for pgbouncer compatibility
            bet_data = self._extract_bet_data(opportunity, bet_id)

            insert_sql = text(
                """
                INSERT INTO bets (
                    bet_id, sport, league, event_name, home_team, away_team,
                    player_name, bet_type, market_description, parameters,
                    outcome_side, event_time, sha_key, created_at, updated_at
                ) VALUES (
                    :bet_id, :sport, :league, :event_name, :home_team, :away_team,
                    :player_name, :bet_type, :market_description, :parameters,
                    :outcome_side, :event_time, :sha_key, :created_at, :updated_at
                )
            """
            )

            # Convert parameters to JSON string for raw SQL
            bet_data_sql = {
                **bet_data,
                "parameters": json.dumps(bet_data.get("parameters", {})),
            }

            await session.execute(insert_sql, bet_data_sql)

            logger.debug(f"Created new bet record: {bet_id}")
            return {"bet_id": bet_id, "created": True}
        else:
            # Update timestamp on existing bet
            await session.execute(
                text("UPDATE bets SET updated_at = :now WHERE bet_id = :bet_id"),
                {"now": datetime.now(), "bet_id": bet_id},
            )

            logger.debug(f"Updated existing bet record: {bet_id}")
            return {"bet_id": bet_id, "created": False}

    async def _create_offer_record(
        self, session: AsyncSession, bet_id: str, opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new offer record for this snapshot using raw SQL"""
        try:
            offer_data = self._extract_offer_data(opportunity, bet_id)

            insert_sql = text(
                """
                INSERT INTO bet_offers (
                    offer_id, bet_id, book, odds, expected_value, fair_odds,
                    implied_probability, confidence_score, volume_indicator,
                    available_limits, offer_metadata, timestamp, refresh_cycle_id
                ) VALUES (
                    :offer_id, :bet_id, :book, :odds, :expected_value, :fair_odds,
                    :implied_probability, :confidence_score, :volume_indicator,
                    :available_limits, :offer_metadata, :timestamp, :refresh_cycle_id
                )
            """
            )

            # Convert JSON fields to strings for raw SQL
            offer_data_sql = {
                **offer_data,
                "odds": json.dumps(offer_data.get("odds", {})),
                "fair_odds": json.dumps(offer_data.get("fair_odds", {})),
                "available_limits": (
                    json.dumps(offer_data.get("available_limits"))
                    if offer_data.get("available_limits")
                    else None
                ),
                "offer_metadata": json.dumps(offer_data.get("offer_metadata", {})),
            }

            await session.execute(insert_sql, offer_data_sql)

            logger.debug(f"Created offer record for bet: {bet_id}")
            return {"created": True}

        except Exception as e:
            logger.warning(f"Failed to create offer for bet {bet_id}: {e}")
            return {"created": False, "error": str(e)}

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

    def _parse_teams(self, event_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse team names from event string"""
        if " vs " in event_name:
            parts = event_name.split(" vs ")
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        elif " @ " in event_name:
            parts = event_name.split(" @ ")
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()  # home @ away
        return None, None

    def _extract_player_name(self, opportunity: Dict[str, Any]) -> Optional[str]:
        """Extract player name for prop bets"""
        description = opportunity.get("Bet Description", "")
        # Simple heuristic: if it contains common prop terms, try to extract name
        prop_keywords = ["points", "rebounds", "assists", "hits", "strikeouts", "goals"]
        if any(keyword in description.lower() for keyword in prop_keywords):
            # Extract the first part before the prop type
            words = description.split()
            if len(words) >= 2:
                # Assume first 1-2 words are player name
                potential_name = " ".join(words[:2])
                if not any(keyword in potential_name.lower() for keyword in prop_keywords):
                    return potential_name
        return None

    def _determine_sport(self, opportunity: Dict[str, Any]) -> str:
        """Determine sport ID from opportunity data"""
        # This could be enhanced with more sophisticated logic
        # For now, use a simple mapping based on common patterns
        description = opportunity.get("Bet Description", "").lower()
        event = opportunity.get("Event", "").lower()

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

        # MLB/Baseball patterns
        if any(
            term in description or term in event
            for term in ["mlb", "baseball", "hits", "strikeouts"]
        ):
            return "baseball_mlb"

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
        """Parse odds data into structured format"""
        best_odds = opportunity.get("Best Available Odds", "+100")

        # Convert American odds to decimal - handle sign properly
        if best_odds.startswith("-"):
            american_int = -int(best_odds[1:])
        else:
            american_int = int(best_odds.replace("+", ""))
        decimal_odds = MathUtils.american_to_decimal(american_int)

        return {
            "american": best_odds,
            "decimal": decimal_odds,
            "source": opportunity.get("Best_Odds_Source", "unknown"),
        }

    def _parse_fair_odds(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fair odds data"""
        fair_odds = opportunity.get("Fair Odds", "+100")
        # Convert American odds to decimal - handle sign properly
        if fair_odds.startswith("-"):
            american_int = -int(fair_odds[1:])
        else:
            american_int = int(fair_odds.replace("+", ""))
        decimal_odds = MathUtils.american_to_decimal(american_int)

        return {"american": fair_odds, "decimal": decimal_odds}

    # Use centralized odds utilities instead of duplicate implementation

    def _determine_book(self, opportunity: Dict[str, Any]) -> str:
        """Determine bookmaker ID from opportunity"""
        source = opportunity.get("Best_Odds_Source", "unknown")

        # Normalize common bookmaker names
        book_mapping = {
            "draftkings": "draftkings",
            "fanduel": "fanduel",
            "betmgm": "betmgm",
            "caesars": "caesars",
            "pointsbet": "pointsbet",
        }

        source_lower = source.lower()
        for key, value in book_mapping.items():
            if key in source_lower:
                return value

        return source.lower().replace(" ", "_") if source != "unknown" else "unknown"

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

    async def _ensure_lookup_data(self, session: AsyncSession):
        """Ensure basic lookup data exists in the database using raw SQL for pgbouncer compatibility"""
        try:
            # Use raw SQL to avoid prepared statement caching issues

            # Create basic sports if they don't exist
            sports_sql = """
                INSERT INTO sports (sport_id, name, category) VALUES
                ('americanfootball_nfl', 'NFL', 'americanfootball'),
                ('basketball_nba', 'NBA', 'basketball'),
                ('baseball_mlb', 'MLB', 'baseball'),
                ('icehockey_nhl', 'NHL', 'icehockey'),
                ('unknown', 'Unknown Sport', 'unknown')
                ON CONFLICT (sport_id) DO NOTHING
            """
            await session.execute(text(sports_sql))

            # Create basic leagues
            leagues_sql = """
                INSERT INTO leagues (league_id, name, sport_id) VALUES
                ('nfl', 'National Football League', 'americanfootball_nfl'),
                ('nba', 'National Basketball Association', 'basketball_nba'),
                ('mlb', 'Major League Baseball', 'baseball_mlb'),
                ('nhl', 'National Hockey League', 'icehockey_nhl'),
                ('unknown', 'Unknown League', 'unknown')
                ON CONFLICT (league_id) DO NOTHING
            """
            await session.execute(text(leagues_sql))

            # Create basic books
            books_sql = """
                INSERT INTO books (book_id, name, book_type, region) VALUES
                ('draftkings', 'DraftKings', 'us_book', 'us'),
                ('fanduel', 'FanDuel', 'us_book', 'us'),
                ('betmgm', 'BetMGM', 'us_book', 'us'),
                ('caesars', 'Caesars', 'us_book', 'us'),
                ('unknown', 'Unknown Book', 'us_book', 'us')
                ON CONFLICT (book_id) DO NOTHING
            """
            await session.execute(text(books_sql))

            logger.debug("Ensured lookup data exists")

        except Exception as e:
            logger.warning(f"Failed to ensure lookup data: {e}")
            # Don't fail the whole operation for lookup data issues


# Global instance for easy access
bet_persistence = BetPersistenceService()

"""
Centralized bet identification and matching utilities
All bet matching logic should flow through here to ensure consistency across
the entire system
"""

from typing import Any, Dict, List, Optional, Tuple

from utils.math_utils import MathUtils


class BetMatcher:
    """Centralized bet identification and matching for consistent behavior
    across the system"""

    @staticmethod
    def create_bet_identifier(outcome: Dict[str, Any], market_key: str = None) -> str:
        """
        Create a unique identifier for a bet outcome

        This is the SINGLE source of truth for how bets are identified across
        the entire system.
        All matching logic should use this function to ensure consistency.

        Args:
            outcome: Outcome dict with name, description, point, etc.
            market_key: Market type (e.g., 'batter_hits', 'player_points')

        Returns:
            Unique identifier string like
            "zach neto|batter_stolen_bases|0.5|over"
        """
        description = outcome.get("description", "").strip().lower()
        name = outcome.get("name", "").strip().lower()
        point = outcome.get("point")

        # For player props, include player name, market type, point, and
        # over/under
        if market_key and (
            market_key.startswith("player_")
            or market_key.startswith("batter_")
            or market_key.startswith("pitcher_")
        ):
            point_str = str(point) if point is not None else "none"
            return f"{description}|{market_key}|{point_str}|{name}"
        else:
            # For regular markets, just use name and point if available
            point_str = str(point) if point is not None else "none"
            return f"{name}|{point_str}"

    @staticmethod
    def find_outcome_by_name(
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find the first outcome that matches the given name"""
        for bookmaker_key, outcomes in market_odds.items():
            for outcome in outcomes:
                if outcome.get("name", "").strip().lower() == outcome_name.strip().lower():
                    return (bookmaker_key, outcome)
        return None

    @staticmethod
    def create_target_identifier(
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
    ) -> Optional[str]:
        """Create target identifier by finding a matching outcome in the
        market data"""
        result = BetMatcher.find_outcome_by_name(outcome_name, market_odds, market_key)
        if result:
            _, outcome = result
            return BetMatcher.create_bet_identifier(outcome, market_key)
        return None

    @staticmethod
    def find_matching_outcomes(
        target_identifier: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Find all outcomes that match the target identifier"""
        matches = []
        for bookmaker_key, outcomes in market_odds.items():
            for outcome in outcomes:
                outcome_identifier = BetMatcher.create_bet_identifier(outcome, market_key)
                if outcome_identifier == target_identifier:
                    matches.append((bookmaker_key, outcome))
        return matches

    @staticmethod
    def find_best_odds(
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
        bookmaker_priority: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, float, int]]:
        """Find the best odds for a specific outcome across all bookmakers"""
        target_identifier = BetMatcher.create_target_identifier(
            outcome_name, market_odds, market_key
        )
        if not target_identifier:
            return None

        matching_outcomes = BetMatcher.find_matching_outcomes(
            target_identifier, market_odds, market_key
        )

        best_decimal_odds = None
        best_bookmaker = None
        best_american_odds = None

        # Check outcomes in bookmaker priority order if specified
        if bookmaker_priority:
            for bookmaker in bookmaker_priority:
                for bm_key, outcome in matching_outcomes:
                    if bm_key == bookmaker:
                        decimal_odds = outcome.get("price")
                        if decimal_odds and decimal_odds > 1.0:
                            if best_decimal_odds is None or decimal_odds > best_decimal_odds:
                                best_decimal_odds = decimal_odds
                                best_bookmaker = bm_key
                                best_american_odds = MathUtils.decimal_to_american(decimal_odds)
        else:
            # No priority, just find the best odds
            for bm_key, outcome in matching_outcomes:
                decimal_odds = outcome.get("price")
                if decimal_odds and decimal_odds > 1.0:
                    if best_decimal_odds is None or decimal_odds > best_decimal_odds:
                        best_decimal_odds = decimal_odds
                        best_bookmaker = bm_key
                        best_american_odds = MathUtils.decimal_to_american(decimal_odds)

        return (best_bookmaker, best_decimal_odds, best_american_odds) if best_bookmaker else None

    @staticmethod
    def count_major_books(
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
        major_books: Optional[List[str]] = None,
    ) -> int:
        """Count how many major books offer a specific outcome"""
        if not major_books:
            from core.config.sports import SportsConfig

            major_books = SportsConfig.MAJOR_BOOKS

        target_identifier = BetMatcher.create_target_identifier(
            outcome_name, market_odds, market_key
        )
        if not target_identifier:
            return 0

        count = 0
        for major_book in major_books:
            if major_book not in market_odds:
                continue

            for outcome in market_odds[major_book]:
                outcome_identifier = BetMatcher.create_bet_identifier(outcome, market_key)
                if outcome_identifier == target_identifier:
                    count += 1
                    break

        return count

    @staticmethod
    def format_all_odds(
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
    ) -> str:
        """Format all available odds for an outcome as a display string"""
        target_identifier = BetMatcher.create_target_identifier(
            outcome_name, market_odds, market_key
        )
        if not target_identifier:
            return "N/A"

        matching_outcomes = BetMatcher.find_matching_outcomes(
            target_identifier, market_odds, market_key
        )

        odds_list = []
        for bookmaker_key, outcome in matching_outcomes:
            price = outcome.get("price", 0)
            if price > 1.0:
                american_odds = MathUtils.decimal_to_american(price)
                display_name = _get_bookmaker_display_name(bookmaker_key)

                # Apply exchange fees for exchanges
                exchanges = ["novig", "prophetx"]
                if bookmaker_key.lower() in exchanges:
                    exchange_fee = 0.02  # 2% commission
                    adjusted_decimal = MathUtils.apply_exchange_fee(price, exchange_fee)
                    adjusted_american = MathUtils.decimal_to_american(adjusted_decimal)
                    odds_str = f"{american_odds:+d} ({adjusted_american:+d})"
                else:
                    odds_str = f"{american_odds:+d}"

                odds_list.append(f"{display_name}: {odds_str}")

        return "; ".join(odds_list) if odds_list else "N/A"

    @staticmethod
    def count_major_books_with_both_sides(
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
        major_books: Optional[List[str]] = None,
    ) -> int:
        """
        Count how many major books offer BOTH sides of a two-sided
        market

        For props: checks if the same player has both Over and Under at
        the same point
        For regular markets: checks if both outcomes exist

        Returns: Number of major books that have complete two-sided coverage
        """
        if not major_books:
            from core.config.sports import SportsConfig

            major_books = SportsConfig.MAJOR_BOOKS

        count = 0

        for major_book in major_books:
            if major_book not in market_odds:
                continue

            outcomes = market_odds[major_book]
            if not outcomes or len(outcomes) < 2:
                continue

            # For player/pitcher/batter props, group by player and check for
            # over/under pairs
            if market_key and (
                market_key.startswith("player_")
                or market_key.startswith("batter_")
                or market_key.startswith("pitcher_")
            ):
                # Group outcomes by player (description) and point
                players: Dict[str, set] = {}
                for outcome in outcomes:
                    description = outcome.get("description", "").strip().lower()
                    name = outcome.get("name", "").strip().lower()
                    point = outcome.get("point")

                    if not description or not name or point is None:
                        continue

                    key = f"{description}|{point}"
                    if key not in players:
                        players[key] = set()
                    players[key].add(name)

                # Check if any player has both over and under at the same point
                has_complete_pair = False
                for player_outcomes in players.values():
                    if "over" in player_outcomes and "under" in player_outcomes:
                        has_complete_pair = True
                        break

                if has_complete_pair:
                    count += 1

            else:
                # For regular markets (h2h, spreads, totals), just check for 2
                # different outcomes
                outcome_names = {outcome.get("name", "").strip().lower() for outcome in outcomes}
                if len(outcome_names) >= 2:
                    count += 1

        return count


def _get_bookmaker_display_name(bookmaker_key: str) -> str:
    """Get display name for bookmaker"""
    display_names = {
        "draftkings": "DraftKings",
        "fanduel": "FanDuel",
        "pinnacle": "Pinnacle",
        "bovada": "Bovada",
        "betmgm": "BetMGM",
        "pointsbetus": "PointsBet",
        "williamhill_us": "WilliamHill",
        "betrivers": "BetRivers",
        "novig": "Novig",
        "prophetx": "ProphetX",
    }
    return display_names.get(bookmaker_key, bookmaker_key.title())

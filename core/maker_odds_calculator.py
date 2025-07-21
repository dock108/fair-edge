"""
Maker Odds Calculator for exchange posting recommendations
Calculates optimal posting odds with 4.5% margin and recommends exchange selection
"""
import logging
from typing import Any, Dict, List, Optional

from utils.math_utils import MathUtils

from .fair_odds_calculator import FairOddsCalculator

logger = logging.getLogger(__name__)


class MakerOddsCalculator:
    """
    Calculator for exchange posting recommendations (maker odds)

    Strategy:
    - Target 4.5% net EV after exchange commission using correct relative margin
    - Use unified math utilities for all conversions and EV calculations
    - Select optimal exchange based on market conditions
    """

    def __init__(self, target_margin: float = 0.045):
        """
        Initialize Maker Odds Calculator

        Args:
            target_margin: Target net EV after fees (default 4.5%)
        """
        self.target_margin = target_margin
        self.calculator = FairOddsCalculator()
        self.exchanges = ["novig", "prophetx"]
        self.exchange_fees = {"novig": 0.02, "prophetx": 0.02}  # Default 2% fees

    def calculate_maker_odds_for_outcome(
        self, fair_american_odds: int, side: str = "back", exchange_fee: float = 0.02
    ) -> Dict[str, Any]:
        """
        Calculate maker odds for a specific outcome and side

        Args:
            fair_american_odds: Fair American odds for the outcome
            side: 'back' or 'lay' side
            exchange_fee: Exchange commission rate (default 2% for most exchanges)

        Returns:
            Dict with maker odds and EV calculations, compatible with data_processor expectations
        """
        if fair_american_odds == 0:
            return {}

        # Convert fair American odds to probability
        fair_probability = MathUtils.american_to_probability(fair_american_odds)

        if side == "lay":
            # For lay side, use the opposite probability
            fair_probability = 1.0 - fair_probability

        # Calculate maker odds using unified math utilities
        maker_result = MathUtils.calculate_maker_odds(
            fair_probability, self.target_margin, exchange_fee
        )

        # Return structure compatible with data_processor expectations
        return {
            "decimal": maker_result["decimal"],
            "american": maker_result["american"],
            "maker_american_odds": maker_result["american"],  # For backward compatibility
            "gross_ev": maker_result["gross_ev"],
            "net_ev": maker_result["net_ev"],
            "maker_probability": maker_result["maker_probability"],
            "target_margin": self.target_margin,
            "exchange_fee": exchange_fee,
            "side": side,
        }

    def calculate_both_sides_maker_odds(
        self, fair_odds_result: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate maker odds for both sides of each outcome

        Args:
            fair_odds_result: Fair odds calculation result

        Returns:
            Dict mapping outcome names to their maker odds for both sides
        """
        if not fair_odds_result or not fair_odds_result.get("outcomes"):
            return {}

        both_sides_odds = {}

        for outcome_name, fair_american_odds in fair_odds_result["outcomes"].items():
            both_sides_odds[outcome_name] = {
                "back": self.calculate_maker_odds_for_outcome(fair_american_odds, "back"),
                "lay": self.calculate_maker_odds_for_outcome(fair_american_odds, "lay"),
            }

        return both_sides_odds

    def get_exchange_market_condition(
        self, outcome_name: str, market_odds: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Check current market conditions on each exchange for an outcome

        Args:
            outcome_name: Name of the outcome to check
            market_odds: Dict mapping bookmaker_key to list of outcomes

        Returns:
            Dict mapping exchange names to their best odds (or None if no market)
        """
        exchange_conditions: Dict[str, Optional[Dict[str, Any]]] = {}

        for exchange in self.exchanges:
            if exchange not in market_odds:
                exchange_conditions[exchange] = None
                continue

            # Find best odds for this outcome on this exchange
            best_odds = None
            outcomes = market_odds[exchange]

            for outcome in outcomes:
                if outcome.get("name", "").strip().lower() == outcome_name.strip().lower():
                    decimal_odds = outcome.get("price")
                    if decimal_odds and decimal_odds > 1.0:
                        american_odds = MathUtils.decimal_to_american(decimal_odds)
                        best_odds = {"decimal": decimal_odds, "american": american_odds}
                        break

            exchange_conditions[exchange] = best_odds

        return exchange_conditions

    def recommend_exchange(
        self,
        outcome_name: str,
        fair_american_odds: int,
        market_odds: Dict[str, List[Dict[str, Any]]],
    ) -> str:
        """
        Recommend which exchange to post on based on market conditions

        Args:
            outcome_name: Name of the outcome
            fair_american_odds: Fair odds for the outcome
            market_odds: Current market odds

        Returns:
            Exchange name recommendation with reasoning
        """
        exchange_conditions = self.get_exchange_market_condition(outcome_name, market_odds)

        novig_market = exchange_conditions.get("novig")
        prophetx_market = exchange_conditions.get("prophetx")

        # Case 1: No market on either exchange
        if novig_market is None and prophetx_market is None:
            return "Post on Novig (No existing markets)"

        # Case 2: One has market, other doesn't
        if novig_market is None and prophetx_market is not None:
            return "Post on Novig (No competition)"
        elif novig_market is not None and prophetx_market is None:
            return "Post on ProphetX (No competition)"

        # Case 3: Both have markets - choose based on "room" from fair odds
        fair_probability = MathUtils.american_to_probability(fair_american_odds)
        fair_decimal = MathUtils.probability_to_decimal(fair_probability)

        # Calculate how far each exchange's odds are from fair value
        novig_distance = abs(novig_market["decimal"] - fair_decimal)
        prophetx_distance = abs(prophetx_market["decimal"] - fair_decimal)

        # Choose the exchange that's further from fair (more room to post)
        if novig_distance > prophetx_distance:
            return f"Post on Novig (More room vs fair: {novig_distance:.3f} vs {prophetx_distance:.3f})"
        elif prophetx_distance > novig_distance:
            return f"Post on ProphetX (More room vs fair: {prophetx_distance:.3f} vs {novig_distance:.3f})"
        else:
            return "Post on Novig (Equal room, default choice)"

    def format_maker_odds_display(self, maker_odds: Dict[str, Any], side_label: str = None) -> str:
        """
        Format maker odds for display using new data structure

        Args:
            maker_odds: Maker odds calculation result
            side_label: Optional label for the side ('Back' or 'Lay')

        Returns:
            Formatted string like "Back: +285 (1.85) | Net EV: +4.5%"
        """
        american = maker_odds.get("american", 0)
        decimal = maker_odds.get("decimal", 1.0)
        net_ev = maker_odds.get("net_ev", 0.0)

        # Format American odds with + sign for positive
        american_str = MathUtils.format_american_odds(american)

        # Format the display
        side_prefix = f"{side_label}: " if side_label else ""
        ev_display = MathUtils.format_ev_percentage(net_ev)
        return f"{side_prefix}{american_str} ({decimal:.2f}) | Net EV: {ev_display}"

    def get_posting_recommendations(
        self, fair_odds_result: Dict[str, Any], market_odds: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Get complete posting recommendations for all outcomes

        Args:
            fair_odds_result: Fair odds calculation result
            market_odds: Current market odds

        Returns:
            Complete posting recommendations with exchange selections
        """
        if not fair_odds_result or not fair_odds_result.get("outcomes"):
            return {"error": "No fair odds available for posting recommendations"}

        recommendations: Dict[str, Dict[str, Any]] = {"outcomes": {}}

        # Calculate maker odds for both sides of each outcome
        both_sides_odds = self.calculate_both_sides_maker_odds(fair_odds_result)

        for outcome_name, fair_american_odds in fair_odds_result["outcomes"].items():
            # Get exchange recommendation
            exchange_rec = self.recommend_exchange(outcome_name, fair_american_odds, market_odds)

            # Get maker odds for both sides
            maker_odds = both_sides_odds.get(outcome_name, {})

            recommendations["outcomes"][outcome_name] = {
                "fair_odds": {
                    "american": fair_american_odds,
                    "probability": MathUtils.american_to_probability(fair_american_odds),
                },
                "maker_odds": {
                    "back": maker_odds.get("back", {}),
                    "lay": maker_odds.get("lay", {}),
                },
                "exchange_recommendation": exchange_rec,
                "exchange_conditions": self.get_exchange_market_condition(
                    outcome_name, market_odds
                ),
            }

        return recommendations

    def format_posting_summary(self, outcome_name: str, posting_data: Dict[str, Any]) -> List[str]:
        """
        Format posting recommendation summary for an outcome

        Args:
            outcome_name: Name of the outcome
            posting_data: Posting recommendation data for the outcome

        Returns:
            List of formatted strings for display
        """
        lines = []

        fair_odds = posting_data.get("fair_odds", {})
        maker_odds = posting_data.get("maker_odds", {})
        exchange_rec = posting_data.get("exchange_recommendation", "Unknown")

        lines.append(f"📋 POSTING RECOMMENDATION: {outcome_name.upper()}")
        lines.append(
            f"   Fair odds: {fair_odds.get('american', 'N/A'):+d} ({fair_odds.get('probability', 0):.1%} prob)"
        )

        # Show both back and lay options
        if "back" in maker_odds and maker_odds["back"]:
            back_display = self.format_maker_odds_display(maker_odds["back"], "Back")
            lines.append(f"   {back_display}")

        if "lay" in maker_odds and maker_odds["lay"]:
            lay_display = self.format_maker_odds_display(maker_odds["lay"], "Lay")
            lines.append(f"   {lay_display}")

        lines.append(f"   📍 {exchange_rec}")

        return lines

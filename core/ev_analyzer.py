"""
Expected Value (EV) Analyzer for Sports Betting

This module implements the core expected value analysis engine for Fair-Edge,
a sports betting arbitrage and positive expected value (EV) detection platform.

The EVAnalyzer class calculates expected value opportunities by comparing
fair odds (calculated using no-vig methodology) against market odds from
various sportsbooks and exchanges. It provides comprehensive analysis including:

- EV percentage calculations with exchange fee adjustments
- Opportunity classification (Take/Marginal/No EV)
- Best odds discovery across multiple platforms
- Exchange-specific fee handling for accurate profitability assessment

Key Features:
- Supports major sportsbooks: Pinnacle, DraftKings, FanDuel
- Handles betting exchanges: Novig, ProphetX with commission adjustments
- Implements robust bet matching across different outcome naming conventions
- Provides deployment-ready error handling and logging

Mathematical Foundation:
- EV Formula: EV = (fair_probability × market_decimal_odds) - 1
- Exchange EV: Adjusted for commission fees on profit only
- Classification thresholds: 4.5% for "Take", 0% for positive EV boundary

Deployment Notes:
- Thread-safe for concurrent analysis requests
- Optimized for real-time odds processing
- Comprehensive error handling for production reliability
- Extensive logging for monitoring and debugging
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from utils.bet_matching import BetMatcher
from utils.math_utils import MathUtils

from .fair_odds_calculator import FairOddsCalculator

logger = logging.getLogger(__name__)


class EVAnalyzer:
    """
    Analyzer for Expected Value opportunities in sports betting

    EV Formula: EV = (p_fair × odds_decimal) - 1
    Classification:
    - Green (Take @ Site): EV ≥ 4.5%
    - Amber (Good, but Try Better): 0% < EV < 4.5%
    - Grey (No +EV to Take): EV ≤ 0%
    """

    def __init__(self, ev_threshold: float = 0.045):
        """
        Initialize EV Analyzer with configurable thresholds and dependencies.

        The EVAnalyzer requires a FairOddsCalculator for computing no-vig odds
        and maintains exchange fee rates for accurate profitability calculations.

        Args:
            ev_threshold (float): Minimum EV threshold for "Take" recommendations.
                                Default 0.045 represents 4.5% expected value,
                                which accounts for typical variance and provides
                                sufficient edge for profitable betting.

        Attributes:
            calculator (FairOddsCalculator): Instance for computing fair odds
            exchange_fees (dict): Commission rates for betting exchanges
                                 - novig: 2% commission on winnings
                                 - prophetx: 2% commission on winnings

        Production Notes:
            - Thread-safe initialization for concurrent requests
            - Exchange fees should be updated if platforms change commission rates
            - EV threshold can be adjusted based on bankroll management strategy
        """
        self.ev_threshold = ev_threshold
        self.calculator = FairOddsCalculator()  # For computing no-vig fair odds
        # Exchange commission rates - critical for accurate EV calculations
        # Fees are charged on profit only when bets win
        self.exchange_fees = {"novig": 0.02, "prophetx": 0.02}  # 2% commission rates

    # Removed redundant wrapper methods - use MathUtils directly

    def calculate_ev_percentage(
        self, fair_probability: float, market_decimal_odds: float, exchange_fee: float = 0.0
    ) -> float:
        """
        Calculate Expected Value percentage with comprehensive fee handling.

        This is the core EV calculation method that determines the profitability
        of betting opportunities. It handles both traditional sportsbooks and
        betting exchanges with their respective fee structures.

        Mathematical Foundation:
        - Gross EV: EV = (fair_probability × market_decimal_odds) - 1
        - Net EV (exchanges): EV = (fair_probability × fee_adjusted_odds) - 1
        - Fee adjustment: net_odds = 1 + (market_odds - 1) × (1 - fee_rate)

        Args:
            fair_probability (float): True win probability derived from no-vig calculation.
                                    Must be between 0.0 and 1.0 (exclusive).
            market_decimal_odds (float): Current market odds in decimal format.
                                       Must be > 1.0 for valid betting odds.
            exchange_fee (float, optional): Commission rate for betting exchanges.
                                          - 0.0 for traditional sportsbooks
                                          - 0.02 for 2% exchange commission
                                          Default: 0.0

        Returns:
            float: Expected value as decimal (e.g., 0.10 = 10% EV)
                  Returns -1.0 for invalid inputs (boundary condition)

        Raises:
            No exceptions raised - invalid inputs return -1.0 for graceful handling

        Production Notes:
            - Optimized for high-frequency calculations during odds processing
            - Input validation ensures mathematical stability
            - Delegates to MathUtils for consistent calculation logic

        Example:
            >>> analyzer = EVAnalyzer()
            >>> ev = analyzer.calculate_ev_percentage(0.45, 2.5, 0.02)  # 45% prob, 2.5 odds, 2% fee
            >>> print(f"EV: {ev*100:.2f}%")  # Output: EV: 8.10%
        """
        # Input validation - ensure mathematically valid probabilities and odds
        if fair_probability <= 0 or fair_probability >= 1 or market_decimal_odds <= 1.0:
            return -1.0  # Sentinel value for invalid inputs (graceful degradation)

        # Delegate to unified math utilities for consistent EV calculation
        # Handles both gross EV (sportsbooks) and net EV (exchanges with fees)
        return MathUtils.calculate_ev_net(fair_probability, market_decimal_odds, exchange_fee)

    def find_best_odds_for_outcome(
        self,
        outcome_name: str,
        market_odds: Dict[str, List[Dict[str, Any]]],
        market_key: str = None,
    ) -> Optional[Tuple[str, float, int]]:
        """
        Find the best decimal odds available for a specific outcome across all platforms

        Args:
            outcome_name: Name of the outcome to search for
            market_odds: Dict mapping bookmaker_key to list of outcomes
            market_key: Market type (e.g., 'player_points') to help with matching

        Returns:
            Tuple of (bookmaker_key, decimal_odds, american_odds) or None if not found
        """
        # Use centralized matching with proper priority order
        all_platforms = ["pinnacle", "draftkings", "fanduel", "novig", "prophetx"]
        return BetMatcher.find_best_odds(outcome_name, market_odds, market_key, all_platforms)

    def classify_ev_opportunity(self, ev_percentage: float) -> Dict[str, Any]:
        """
        Classify EV opportunity based on percentage thresholds

        Args:
            ev_percentage: EV as decimal (e.g., 0.045 = 4.5%)

        Returns:
            Dict with classification details
        """
        if ev_percentage >= self.ev_threshold:
            return {
                "category": "take",
                "color": "green",
                "action": "Take",
                "description": "Strong +EV opportunity above threshold",
            }
        elif ev_percentage > 0:
            return {
                "category": "marginal",
                "color": "amber",
                "action": "Good, but Try Better",
                "description": "Positive EV but below threshold",
            }
        else:
            return {
                "category": "no_ev",
                "color": "grey",
                "action": "No +EV to Take",
                "description": "No positive expected value available",
            }

    def analyze_market_opportunities(
        self,
        market_odds: Dict[str, List[Dict[str, Any]]],
        fair_odds_result: Dict[str, Any],
        market_key: str = None,
    ) -> Dict[str, Any]:
        """
        Analyze all outcomes in a market for EV opportunities

        Args:
            market_odds: Dict mapping bookmaker_key to list of outcomes
            fair_odds_result: Fair odds calculation result from FairOddsCalculator
            market_key: Market type (e.g., 'player_points') for better matching

        Returns:
            Dict with EV analysis for each outcome
        """
        if not fair_odds_result or not fair_odds_result.get("outcomes"):
            return {"error": "No fair odds available for analysis"}

        analysis: Dict[str, Any] = {
            "market_summary": {"anchor_books": fair_odds_result.get("anchor_books", {})},
            "outcomes": {},
        }

        # Analyze each outcome
        for outcome_name, fair_american_odds in fair_odds_result["outcomes"].items():
            # Calculate fair probability
            fair_probability = MathUtils.american_to_probability(fair_american_odds)

            # Find best available odds for this outcome with proper matching
            best_odds_data = self.find_best_odds_for_outcome(outcome_name, market_odds, market_key)

            if best_odds_data:
                best_bookmaker, best_decimal_odds, best_american_odds = best_odds_data

                # Calculate exchange adjustments if applicable
                exchange_data = self.calculate_exchange_adjusted_odds(
                    best_decimal_odds, best_bookmaker
                )

                # Calculate EV with original odds
                ev_percentage_original = self.calculate_ev_percentage(
                    fair_probability, best_decimal_odds
                )

                # Calculate EV with fee-adjusted odds if it's an exchange
                if exchange_data["is_exchange"]:
                    # Use adjusted decimal odds (fees already applied) with no additional fee
                    ev_percentage_adjusted = self.calculate_ev_percentage(
                        fair_probability, exchange_data["adjusted_decimal"], 0.0
                    )
                else:
                    ev_percentage_adjusted = ev_percentage_original

                # Use adjusted EV for classification
                classification = self.classify_ev_opportunity(ev_percentage_adjusted)

                # Store outcome analysis with both pre-fee and post-fee data
                analysis["outcomes"][outcome_name] = {
                    "fair_odds": {"american": fair_american_odds, "probability": fair_probability},
                    "best_market_odds": {
                        "bookmaker": best_bookmaker,
                        "american": best_american_odds,
                        "decimal": best_decimal_odds,
                        "is_exchange": exchange_data["is_exchange"],
                        "exchange_data": exchange_data if exchange_data["is_exchange"] else None,
                    },
                    "ev_analysis": {
                        "ev_percentage": ev_percentage_adjusted,  # Use adjusted for main classification
                        "ev_percentage_original": ev_percentage_original,  # Keep original for display
                        "ev_display": f"{ev_percentage_adjusted*100:+.2f}%",
                        "ev_display_original": f"{ev_percentage_original*100:+.2f}%"
                        if exchange_data["is_exchange"]
                        else None,
                        "classification": classification,
                    },
                }
            else:
                # No market odds found for this outcome
                analysis["outcomes"][outcome_name] = {
                    "fair_odds": {"american": fair_american_odds, "probability": fair_probability},
                    "best_market_odds": None,
                    "ev_analysis": {
                        "ev_percentage": -1.0,
                        "ev_display": "N/A",
                        "classification": {
                            "category": "no_data",
                            "color": "grey",
                            "action": "No Market Data",
                            "description": "No odds available from any platform",
                        },
                    },
                }

        return analysis

    def format_ev_opportunity_display(self, outcome_analysis: Dict[str, Any]) -> str:
        """
        Format EV opportunity for display

        Example outputs:
        - "Take @ Novig (+8.25% EV)"
        - "Good, but Try Better (+2.1% EV)"
        - "No +EV to Take (-1.5% EV)"
        """
        ev_data = outcome_analysis.get("ev_analysis", {})
        classification = ev_data.get("classification", {})
        ev_display = ev_data.get("ev_display", "N/A")

        action = classification.get("action", "Unknown")

        if classification.get("category") == "take":
            best_odds = outcome_analysis.get("best_market_odds", {})
            bookmaker = best_odds.get("bookmaker", "Unknown")
            bookmaker_display = {
                "pinnacle": "Pinnacle",
                "draftkings": "DraftKings",
                "fanduel": "FanDuel",
                "novig": "Novig",
                "prophetx": "ProphetX",
            }.get(bookmaker, bookmaker.title())
            return f"Take @ {bookmaker_display} ({ev_display} EV)"
        else:
            return f"{action} ({ev_display} EV)"

    def get_market_ev_summary(self, ev_analysis: Dict[str, Any]) -> Dict[str, int]:
        """
        Get summary count of EV opportunities by category

        Returns:
            Dict with counts: {'take': 0, 'marginal': 1, 'no_ev': 1, 'no_data': 0}
        """
        summary = {"take": 0, "marginal": 0, "no_ev": 0, "no_data": 0}

        for outcome_data in ev_analysis.get("outcomes", {}).values():
            category = (
                outcome_data.get("ev_analysis", {})
                .get("classification", {})
                .get("category", "no_data")
            )
            if category in summary:
                summary[category] += 1

        return summary

    def calculate_exchange_adjusted_odds(
        self, decimal_odds: float, bookmaker_key: str
    ) -> Dict[str, Any]:
        """
        Calculate exchange-adjusted odds and EV accounting for fees using unified math utils

        Args:
            decimal_odds: Original decimal odds from exchange
            bookmaker_key: Exchange name (prophetx, novig)

        Returns:
            Dict with original and fee-adjusted odds/EV data
        """
        exchanges = ["prophetx", "novig"]
        commission_rate = self.exchange_fees.get(bookmaker_key.lower(), 0.0)

        if bookmaker_key.lower() not in exchanges:
            # Not an exchange, return original odds
            american_odds = MathUtils.decimal_to_american(decimal_odds)
            return {
                "is_exchange": False,
                "original_decimal": decimal_odds,
                "original_american": american_odds,
                "adjusted_decimal": decimal_odds,
                "adjusted_american": american_odds,
                "commission_rate": 0.0,
            }

        # Calculate fee-adjusted odds for exchanges using unified math utils
        adjusted_decimal = MathUtils.apply_exchange_fee(decimal_odds, commission_rate)

        original_american = MathUtils.decimal_to_american(decimal_odds)
        adjusted_american = MathUtils.decimal_to_american(adjusted_decimal)

        return {
            "is_exchange": True,
            "original_decimal": decimal_odds,
            "original_american": original_american,
            "adjusted_decimal": adjusted_decimal,
            "adjusted_american": adjusted_american,
            "commission_rate": commission_rate,
        }

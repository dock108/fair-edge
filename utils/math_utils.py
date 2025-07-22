"""
Unified math utilities for sports betting +EV analysis
Contains all odds conversions, EV calculations, and fee adjustments
Source of truth for mathematical operations - eliminates duplication
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class MathUtils:
    """Centralized mathematical operations for betting analysis"""

    @staticmethod
    def decimal_to_probability(decimal_odds: float) -> float:
        """
        Convert decimal odds to implied probability
        Formula: p = 1 / d
        """
        if decimal_odds <= 1.0:
            return 0.0
        return 1.0 / decimal_odds

    @staticmethod
    def probability_to_decimal(probability: float) -> float:
        """
        Convert probability to decimal odds
        Formula: d = 1 / p
        """
        if probability <= 0.0 or probability >= 1.0:
            return 1.0
        return 1.0 / probability

    @staticmethod
    def american_to_probability(american_odds: int) -> float:
        """
        Convert American odds to implied probability
        Formula:
        - p = 100 / (a + 100) if a > 0
        - p = |a| / (|a| + 100) if a < 0
        """
        if american_odds > 0:
            return 100.0 / (american_odds + 100.0)
        elif american_odds < 0:
            return abs(american_odds) / (abs(american_odds) + 100.0)
        else:
            return 0.0

    @staticmethod
    def probability_to_american(probability: float) -> int:
        """
        Convert probability to American odds
        Formula:
        - If p > 0.5: a = -100 × p / (1 - p)
        - If p = 0.5: a = +100 (even money convention)
        - Else: a = 100 × (1 - p) / p
        """
        if probability <= 0.0 or probability >= 1.0:
            return 0

        # Handle even money edge case (50% probability)
        if abs(probability - 0.5) < 1e-10:
            return 100  # Convention: use +100 for even money

        if probability > 0.5:
            # Negative odds (favorite)
            american = -100.0 * probability / (1.0 - probability)
        else:
            # Positive odds (underdog)
            american = 100.0 * (1.0 - probability) / probability

        # Standard American rounding: nearest whole integer away from zero
        return int(round(american, 0))

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> int:
        """Convert decimal odds to American format via probability"""
        probability = MathUtils.decimal_to_probability(decimal_odds)
        return MathUtils.probability_to_american(probability)

    @staticmethod
    def american_to_decimal(american_odds: int) -> float:
        """Convert American odds to decimal format via probability"""
        probability = MathUtils.american_to_probability(american_odds)
        return MathUtils.probability_to_decimal(probability)

    @staticmethod
    def remove_vig_two_sided(prob1: float, prob2: float) -> Tuple[float, float]:
        """
        Remove vig from two-sided market probabilities
        Formula: fair_p_i = p_i / (p1 + p2)
        """
        total_prob = prob1 + prob2
        if total_prob <= 0.0:
            return 0.0, 0.0

        fair_prob1 = prob1 / total_prob
        fair_prob2 = prob2 / total_prob

        return fair_prob1, fair_prob2

    @staticmethod
    def calculate_ev_gross(fair_probability: float, market_decimal_odds: float) -> float:
        """
        Calculate gross expected value (no fees)
        Formula: EV = p × d - 1
        """
        if fair_probability <= 0.0 or market_decimal_odds <= 1.0:
            return -1.0

        return (fair_probability * market_decimal_odds) - 1.0

    @staticmethod
    def apply_exchange_fee(decimal_odds: float, fee_rate: float) -> float:
        """
        Apply exchange fee to decimal odds (fee charged on profit)
        Formula: net_decimal = 1 + (decimal - 1) × (1 - fee)
        """
        if decimal_odds <= 1.0:
            return decimal_odds

        profit = decimal_odds - 1.0
        net_profit = profit * (1.0 - fee_rate)
        return 1.0 + net_profit

    @staticmethod
    def calculate_ev_net(
        fair_probability: float, market_decimal_odds: float, fee_rate: float = 0.0
    ) -> float:
        """
        Calculate net expected value after exchange fees
        Formula: EV_net = p × net_decimal - 1
        """
        if fee_rate == 0.0:
            return MathUtils.calculate_ev_gross(fair_probability, market_decimal_odds)

        net_decimal = MathUtils.apply_exchange_fee(market_decimal_odds, fee_rate)
        return MathUtils.calculate_ev_gross(fair_probability, net_decimal)

    @staticmethod
    def calculate_maker_probability(
        fair_probability: float, target_ev: float, fee_rate: float = 0.0
    ) -> float:
        """
        Calculate maker probability for target EV after fees using two-stage
        approach

        Stage 1: Calculate 2% EV to cover exchange fees
        Stage 2: Add 2.5% EV buffer for profit margin
        Total: 4.5% but built properly to account for fee structure

        Args:
            fair_probability: True probability of outcome
            target_ev: Total desired EV (typically 0.045 = 4.5%)
            fee_rate: Exchange fee rate (e.g., 0.02 for 2%)
        """
        if fair_probability <= 0.0 or fair_probability >= 1.0:
            return 0.0

        if fee_rate == 0.0:
            # No fees: use simple relative scaling
            maker_prob = fair_probability / (1.0 + target_ev)
        else:
            # Two-stage approach for exchanges:
            # Stage 1: Calculate EV to cover the fee (typically 2%)
            fee_coverage_ev = fee_rate  # 2% EV to cover 2% fee

            # Stage 2: Add profit buffer (typically 2.5%)
            profit_buffer_ev = target_ev - fee_coverage_ev  # 4.5% - 2% = 2.5%

            # First, adjust for fee coverage (2% EV)
            # maker_prob_stage1 = fair_prob / (1 + fee_coverage_ev)
            stage1_prob = fair_probability / (1.0 + fee_coverage_ev)

            # Then, adjust for profit buffer (2.5% EV on top)
            # This creates the final maker probability
            maker_prob = stage1_prob / (1.0 + profit_buffer_ev)

        # Ensure valid probability bounds
        return max(0.05, min(0.95, maker_prob))

    @staticmethod
    def calculate_maker_odds(
        fair_probability: float, target_ev: float, fee_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate maker odds for target EV after fees

        Returns:
            Dict with decimal, american, gross_ev, net_ev
        """
        maker_prob = MathUtils.calculate_maker_probability(fair_probability, target_ev, fee_rate)

        if maker_prob <= 0.0:
            return {
                "decimal": 1.0,
                "american": 0,
                "gross_ev": -1.0,
                "net_ev": -1.0,
                "maker_probability": 0.0,
            }

        decimal_odds = MathUtils.probability_to_decimal(maker_prob)
        american_odds = MathUtils.probability_to_american(maker_prob)

        # Calculate actual EV achieved
        gross_ev = MathUtils.calculate_ev_gross(fair_probability, decimal_odds)
        net_ev = MathUtils.calculate_ev_net(fair_probability, decimal_odds, fee_rate)

        return {
            "decimal": decimal_odds,
            "american": american_odds,
            "gross_ev": gross_ev,
            "net_ev": net_ev,
            "maker_probability": maker_prob,
        }

    @staticmethod
    def format_american_odds(american_odds: int) -> str:
        """Format American odds with proper sign display"""
        if american_odds > 0:
            return f"+{american_odds}"
        elif american_odds < 0:
            return str(american_odds)
        else:
            return "EVEN"

    @staticmethod
    def format_ev_percentage(ev: float) -> str:
        """Format EV as percentage with one decimal place"""
        return f"{ev * 100:+.1f}%"

    @staticmethod
    def validate_conversion_accuracy(american_odds: int, _tolerance: float = 1e-6) -> bool:
        """
        Validate round-trip conversion accuracy
        american -> probability -> american should match within tolerance
        """
        prob = MathUtils.american_to_probability(american_odds)
        back_to_american = MathUtils.probability_to_american(prob)

        # Allow for ±1 tick due to rounding
        return abs(back_to_american - american_odds) <= 1


# All functions now consolidated in MathUtils class - no backward
# compatibility wrappers needed

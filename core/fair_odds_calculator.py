"""
Fair Odds Calculator for Sports Betting +EV Analysis
Calculates no-vig fair odds by removing bookmaker margins
"""
import logging
from core.config.sports import SportsConfig
from typing import Dict, List, Any, Optional, Tuple
from utils.math_utils import MathUtils
from utils.bet_matching import BetMatcher

logger = logging.getLogger(__name__)


class FairOddsCalculator:
    """
    Calculator for fair (no-vig) odds using the anchor book methodology
    
    Algorithm:
    1. Ignore exchange quotes when computing fair odds
    2. For each outcome, find the best payout from major books (Pinnacle, DraftKings, FanDuel)  
    3. Use that same bookmaker's opposite side to maintain market consistency
    4. Convert American odds to probabilities, remove vig, convert back
    """
    
    def __init__(self):
        self.major_books = SportsConfig.MAJOR_BOOKS  # ['pinnacle', 'draftkings', 'fanduel']
    
    # Removed redundant wrapper methods - use MathUtils directly
    
    def find_best_payout_for_outcome(self, outcome_name: str, market_odds: Dict[str, List[Dict[str, Any]]], market_key: str = None) -> Optional[Tuple[str, int]]:
        """
        Find the major book offering the best payout for a specific outcome
        Returns (bookmaker_key, american_odds) or None if not found
        """
        # Use centralized matching with major books priority
        result = BetMatcher.find_best_odds(outcome_name, market_odds, market_key, self.major_books)
        if result:
            bookmaker_key, decimal_odds, american_odds = result
            return (bookmaker_key, american_odds)
        return None
    
    def get_anchor_book_odds_pair(self, outcome_a: str, outcome_b: str, market_odds: Dict[str, List[Dict[str, Any]]], market_key: str = None) -> Dict[str, Tuple[str, int, int]]:
        """
        Get anchor book and odds pair for each outcome
        Returns dict: {outcome_name: (anchor_book, odds_for_outcome, odds_for_opposite)}
        """
        anchor_data = {}
        
        # Find best payout for outcome A
        best_a = self.find_best_payout_for_outcome(outcome_a, market_odds, market_key)
        if best_a:
            anchor_book_a, odds_a = best_a
            # Get the opposite side from the same book
            odds_b_from_a = self._get_opposite_odds(outcome_b, anchor_book_a, market_odds, market_key)
            if odds_b_from_a:
                anchor_data[outcome_a] = (anchor_book_a, odds_a, odds_b_from_a)
        
        # Find best payout for outcome B
        best_b = self.find_best_payout_for_outcome(outcome_b, market_odds, market_key)
        if best_b:
            anchor_book_b, odds_b = best_b
            # Get the opposite side from the same book
            odds_a_from_b = self._get_opposite_odds(outcome_a, anchor_book_b, market_odds, market_key)
            if odds_a_from_b:
                anchor_data[outcome_b] = (anchor_book_b, odds_b, odds_a_from_b)
        
        return anchor_data
    
    def _get_opposite_odds(self, outcome_name: str, bookmaker_key: str, market_odds: Dict[str, List[Dict[str, Any]]], market_key: str = None) -> Optional[int]:
        """Get odds for the opposite outcome from the same bookmaker using exact matching"""
        if bookmaker_key not in market_odds:
            return None
        
        # Use centralized matching logic
        target_identifier = BetMatcher.create_target_identifier(outcome_name, market_odds, market_key)
        if not target_identifier:
            return None
            
        outcomes = market_odds[bookmaker_key]
        for outcome in outcomes:
            outcome_identifier = BetMatcher.create_bet_identifier(outcome, market_key)
            if outcome_identifier == target_identifier:
                decimal_odds = outcome.get('price')
                if decimal_odds and decimal_odds > 1.0:
                    return MathUtils.decimal_to_american(decimal_odds)
        return None
    
    def calculate_fair_odds(self, market_odds: Dict[str, List[Dict[str, Any]]], market_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Calculate fair odds for a two-sided market using anchor book methodology
        
        Args:
            market_odds: Dict mapping bookmaker_key to list of outcomes
            market_key: Market type (e.g., 'player_points') for better matching
            
        Returns:
            Dict with fair odds data or None if calculation fails
        """
        # First, identify the two outcomes
        all_outcome_names = set()
        for outcomes in market_odds.values():
            for outcome in outcomes:
                name = outcome.get('name', '').strip()
                if name:
                    all_outcome_names.add(name)
        
        if len(all_outcome_names) != 2:
            logger.debug(f"Market has {len(all_outcome_names)} outcomes, expected 2")
            return None
        
        outcome_a, outcome_b = list(all_outcome_names)
        
        # Get anchor book data for each outcome with proper matching
        anchor_data = self.get_anchor_book_odds_pair(outcome_a, outcome_b, market_odds, market_key)
        
        if not anchor_data:
            logger.debug("No anchor book data found")
            return None
        
        # Calculate fair odds for each outcome that has anchor data
        fair_odds_result = {
            'outcomes': {},
            'anchor_books': {},
            'raw_probabilities': {}
        }
        
        for outcome_name, (anchor_book, outcome_odds, opposite_odds) in anchor_data.items():
            # Convert to probabilities
            prob_outcome = MathUtils.american_to_probability(outcome_odds)
            prob_opposite = MathUtils.american_to_probability(opposite_odds)
            
            # Remove vig by normalizing probabilities
            total_prob = prob_outcome + prob_opposite
            fair_prob_outcome = prob_outcome / total_prob
            
            # Convert back to American odds
            fair_american_odds = MathUtils.probability_to_american(fair_prob_outcome)
            
            # Store results
            fair_odds_result['outcomes'][outcome_name] = fair_american_odds
            fair_odds_result['anchor_books'][outcome_name] = anchor_book
            fair_odds_result['raw_probabilities'][outcome_name] = {
                'raw': prob_outcome,
                'fair': fair_prob_outcome,
                'total_before_normalization': total_prob
            }
        
        # If we have both outcomes, also store the implied fair odds for the opposite
        if len(fair_odds_result['outcomes']) == 2:
            # Both outcomes calculated from their respective anchor books
            logger.debug(f"Fair odds calculated: {fair_odds_result['outcomes']}")
        elif len(fair_odds_result['outcomes']) == 1:
            # Calculate the missing outcome's fair odds from the one we have
            calculated_outcome = list(fair_odds_result['outcomes'].keys())[0]
            missing_outcome = outcome_a if calculated_outcome == outcome_b else outcome_b
            
            # Use the normalized probability from the calculated outcome
            fair_prob_calculated = fair_odds_result['raw_probabilities'][calculated_outcome]['fair']
            fair_prob_missing = 1.0 - fair_prob_calculated
            fair_american_missing = MathUtils.probability_to_american(fair_prob_missing)
            
            fair_odds_result['outcomes'][missing_outcome] = fair_american_missing
            fair_odds_result['raw_probabilities'][missing_outcome] = {
                'fair': fair_prob_missing
            }
        
        return fair_odds_result
    
    def format_fair_odds_display(self, fair_odds_result: Dict[str, Any]) -> str:
        """
        Format fair odds for display
        Example: "Mets +143 / Yankees -143 (fair)"
        """
        if not fair_odds_result or not fair_odds_result.get('outcomes'):
            return "N/A"
        
        outcomes = fair_odds_result['outcomes']
        formatted_parts = []
        
        for outcome_name, american_odds in outcomes.items():
            if american_odds > 0:
                formatted_parts.append(f"{outcome_name} {MathUtils.format_american_odds(american_odds)}")
            else:
                formatted_parts.append(f"{outcome_name} {MathUtils.format_american_odds(american_odds)}")
        
        result = " / ".join(formatted_parts) + " (fair)"
        return result
    
    def get_all_current_odds_display(self, market_odds: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """
        Get current odds from all sources in American format for display
        Returns dict: {bookmaker: "OutcomeA +odds / OutcomeB -odds" or "N/A"}
        """
        display_odds = {}
        
        for bookmaker_key in ['pinnacle', 'draftkings', 'fanduel', 'novig', 'prophetx']:
            if bookmaker_key in market_odds:
                outcomes = market_odds[bookmaker_key]
                if len(outcomes) == 2:
                    formatted_parts = []
                    for outcome in outcomes:
                        name = outcome.get('name', '')
                        decimal_odds = outcome.get('price')
                        if decimal_odds and decimal_odds > 1.0:
                            american_odds = MathUtils.decimal_to_american(decimal_odds)
                            formatted_parts.append(f"{name} {MathUtils.format_american_odds(american_odds)}")
                        else:
                            formatted_parts.append(f"{name} N/A")
                    
                    display_odds[bookmaker_key] = " / ".join(formatted_parts)
                else:
                    display_odds[bookmaker_key] = "N/A"
            else:
                display_odds[bookmaker_key] = "N/A"
        
        return display_odds 
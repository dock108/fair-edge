"""
Odds Calculator utility functions for sports betting analysis
Updated to use unified math utilities - no longer duplicates conversion logic
"""
import logging
from typing import Dict, List, Any, Optional
from services.config import BOOKMAKERS, EXCHANGE_COMMISSIONS, MAKER_EDGE_MARGIN
from utils.math_utils import MathUtils

logger = logging.getLogger(__name__)


class OddsCalculator:
    """Calculator for odds analysis and +EV identification - now uses unified math utils"""
    
    def __init__(self):
        self.sharp_books = ['pinnacle']  # Books considered "sharp" for fair odds calculation
        self.us_books = ['draftkings', 'fanduel']  # Major US books
        self.exchanges = ['novig', 'prophetx']  # Betting exchanges
        
    def decimal_to_implied_probability(self, decimal_odds: float) -> float:
        """Convert decimal odds to implied probability using unified math utils"""
        return MathUtils.decimal_to_probability(decimal_odds)
    
    def implied_probability_to_decimal(self, probability: float) -> float:
        """Convert implied probability to decimal odds using unified math utils"""
        return MathUtils.probability_to_decimal(probability)
    
    def remove_vig(self, odds_list: List[float]) -> List[float]:
        """Remove vigorish from a set of odds to get fair probabilities"""
        if not odds_list or len(odds_list) < 2:
            return odds_list
        
        if len(odds_list) == 2:
            # For two-sided markets, use the unified vig removal
            prob1 = MathUtils.decimal_to_probability(odds_list[0])
            prob2 = MathUtils.decimal_to_probability(odds_list[1])
            fair_prob1, fair_prob2 = MathUtils.remove_vig_two_sided(prob1, prob2)
            return [MathUtils.probability_to_decimal(fair_prob1), MathUtils.probability_to_decimal(fair_prob2)]
        else:
            # For multi-outcome markets, use the original normalization approach
            implied_probs = [MathUtils.decimal_to_probability(odds) for odds in odds_list]
            total_prob = sum(implied_probs)
            
            if total_prob <= 1.0:
                return odds_list
            
            fair_probs = [prob / total_prob for prob in implied_probs]
            fair_odds = [MathUtils.probability_to_decimal(prob) for prob in fair_probs]
            return fair_odds
    
    def calculate_fair_odds(self, market_odds: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, float]]:
        """
        Calculate fair odds for a market using sharp book data
        Returns dict mapping outcome names to fair decimal odds
        """
        if not market_odds:
            return None
        
        # Priority order: Pinnacle first, then average of DK/FD if Pinnacle not available
        fair_odds = {}
        
        # Try to use Pinnacle (sharp book) first
        if 'pinnacle' in market_odds:
            pinnacle_outcomes = market_odds['pinnacle']
            if len(pinnacle_outcomes) >= 2:
                odds_values = [outcome['price'] for outcome in pinnacle_outcomes]
                fair_odds_values = self.remove_vig(odds_values)
                
                for i, outcome in enumerate(pinnacle_outcomes):
                    fair_odds[outcome['name']] = fair_odds_values[i]
                
                logger.debug("Used Pinnacle for fair odds calculation")
                return fair_odds
        
        # Fallback: Use average of DraftKings and FanDuel
        dk_odds = market_odds.get('draftkings', [])
        fd_odds = market_odds.get('fanduel', [])
        
        if len(dk_odds) >= 2 and len(fd_odds) >= 2:
            # Match outcomes by name and average the odds
            outcome_names = set()
            for outcome in dk_odds + fd_odds:
                outcome_names.add(outcome['name'])
            
            averaged_outcomes = []
            for name in outcome_names:
                dk_price = next((o['price'] for o in dk_odds if o['name'] == name), None)
                fd_price = next((o['price'] for o in fd_odds if o['name'] == name), None)
                
                if dk_price and fd_price:
                    avg_price = (dk_price + fd_price) / 2
                    averaged_outcomes.append({'name': name, 'price': avg_price})
            
            if len(averaged_outcomes) >= 2:
                odds_values = [outcome['price'] for outcome in averaged_outcomes]
                fair_odds_values = self.remove_vig(odds_values)
                
                for i, outcome in enumerate(averaged_outcomes):
                    fair_odds[outcome['name']] = fair_odds_values[i]
                
                logger.debug("Used DK/FD average for fair odds calculation")
                return fair_odds
        
        logger.warning("Could not calculate fair odds - insufficient sharp book data")
        return None
    
    def find_ev_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find positive expected value opportunities in a market
        Returns list of +EV opportunities with details
        """
        opportunities = []
        
        # Extract odds by bookmaker
        market_odds = {}
        for bookmaker_data in market_data.get('bookmakers', []):
            bookmaker_key = bookmaker_data['key']
            if bookmaker_key in [bm['key'] for bm in BOOKMAKERS.values()]:
                for market in bookmaker_data.get('markets', []):
                    market_key = market['key']
                    if market_key not in market_odds:
                        market_odds[market_key] = {}
                    market_odds[market_key][bookmaker_key] = market['outcomes']
        
        # Analyze each market type
        for market_key, bookmaker_outcomes in market_odds.items():
            fair_odds = self.calculate_fair_odds(bookmaker_outcomes)
            if not fair_odds:
                continue
            
            # Check each bookmaker's odds against fair odds
            for bookmaker_key, outcomes in bookmaker_outcomes.items():
                for outcome in outcomes:
                    outcome_name = outcome['name']
                    offered_odds = outcome['price']
                    
                    if outcome_name in fair_odds:
                        fair_price = fair_odds[outcome_name]
                        
                        # Calculate expected value
                        ev_percentage = self.calculate_ev_percentage(offered_odds, fair_price)
                        
                        # Consider +EV if > 1% (to account for fees/variance)
                        if ev_percentage > 1.0:
                            opportunity = {
                                'event_id': market_data.get('id'),
                                'sport': market_data.get('sport_key'),
                                'home_team': market_data.get('home_team'),
                                'away_team': market_data.get('away_team'),
                                'commence_time': market_data.get('commence_time'),
                                'market_type': market_key,
                                'outcome': outcome_name,
                                'bookmaker': bookmaker_key,
                                'bookmaker_name': BOOKMAKERS.get(bookmaker_key, {}).get('name', bookmaker_key),
                                'offered_odds': offered_odds,
                                'fair_odds': fair_price,
                                'ev_percentage': ev_percentage,
                                'action': f"Take bet on {BOOKMAKERS.get(bookmaker_key, {}).get('name', bookmaker_key)}",
                                'description': self._format_bet_description(market_key, outcome, market_data)
                            }
                            opportunities.append(opportunity)
                        elif 0 <= ev_percentage <= 1.0:
                            # Mark as "fair" bet (marginal)
                            opportunity = {
                                'event_id': market_data.get('id'),
                                'sport': market_data.get('sport_key'),
                                'home_team': market_data.get('home_team'),
                                'away_team': market_data.get('away_team'),
                                'commence_time': market_data.get('commence_time'),
                                'market_type': market_key,
                                'outcome': outcome_name,
                                'bookmaker': bookmaker_key,
                                'bookmaker_name': BOOKMAKERS.get(bookmaker_key, {}).get('name', bookmaker_key),
                                'offered_odds': offered_odds,
                                'fair_odds': fair_price,
                                'ev_percentage': ev_percentage,
                                'action': "Fair bet (marginal)",
                                'description': self._format_bet_description(market_key, outcome, market_data)
                            }
                            opportunities.append(opportunity)
        
        return opportunities
    
    def calculate_ev_percentage(self, offered_odds: float, fair_odds: float) -> float:
        """Calculate expected value percentage using unified math utils"""
        if fair_odds <= 1.0 or offered_odds <= 1.0:
            return 0.0
        
        fair_prob = MathUtils.decimal_to_probability(fair_odds)
        ev_decimal = MathUtils.calculate_ev_gross(fair_prob, offered_odds)
        
        # Convert to percentage for backwards compatibility
        return ev_decimal * 100.0
    
    def suggest_market_making_odds(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest odds to post on exchanges when no +EV opportunities exist
        """
        suggestions = []
        
        # Extract odds by bookmaker
        market_odds = {}
        for bookmaker_data in market_data.get('bookmakers', []):
            bookmaker_key = bookmaker_data['key']
            if bookmaker_key in [bm['key'] for bm in BOOKMAKERS.values()]:
                for market in bookmaker_data.get('markets', []):
                    market_key = market['key']
                    if market_key not in market_odds:
                        market_odds[market_key] = {}
                    market_odds[market_key][bookmaker_key] = market['outcomes']
        
        # Analyze each market type
        for market_key, bookmaker_outcomes in market_odds.items():
            fair_odds = self.calculate_fair_odds(bookmaker_outcomes)
            if not fair_odds:
                continue
            
            # Check if any +EV opportunities exist
            has_ev_opportunity = False
            for bookmaker_key, outcomes in bookmaker_outcomes.items():
                for outcome in outcomes:
                    if outcome['name'] in fair_odds:
                        ev = self.calculate_ev_percentage(outcome['price'], fair_odds[outcome['name']])
                        if ev > 1.0:
                            has_ev_opportunity = True
                            break
                if has_ev_opportunity:
                    break
            
            # If no +EV opportunities, suggest market making
            if not has_ev_opportunity:
                for outcome_name, fair_price in fair_odds.items():
                    # Calculate suggested posting odds for each exchange
                    for exchange in self.exchanges:
                        if exchange in EXCHANGE_COMMISSIONS:
                            commission = EXCHANGE_COMMISSIONS[exchange]
                            suggested_odds = self._calculate_maker_odds(fair_price, commission)
                            
                            suggestion = {
                                'event_id': market_data.get('id'),
                                'sport': market_data.get('sport_key'),
                                'home_team': market_data.get('home_team'),
                                'away_team': market_data.get('away_team'),
                                'commence_time': market_data.get('commence_time'),
                                'market_type': market_key,
                                'outcome': outcome_name,
                                'exchange': exchange,
                                'exchange_name': BOOKMAKERS.get(exchange, {}).get('name', exchange),
                                'fair_odds': fair_price,
                                'suggested_odds': suggested_odds,
                                'expected_profit_margin': self._calculate_maker_profit_margin(fair_price, suggested_odds, commission),
                                'action': f"Post on {BOOKMAKERS.get(exchange, {}).get('name', exchange)} at {suggested_odds:.2f}",
                                'description': self._format_bet_description(market_key, {'name': outcome_name}, market_data)
                            }
                            suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_maker_odds(self, fair_odds: float, commission: float) -> float:
        """Calculate suggested odds for market making"""
        fair_prob = self.decimal_to_implied_probability(fair_odds)
        
        # Adjust probability to account for commission and maker edge
        adjusted_prob = fair_prob * (1 + commission + MAKER_EDGE_MARGIN)
        
        # Ensure probability doesn't exceed reasonable bounds
        adjusted_prob = min(adjusted_prob, 0.95)
        
        suggested_odds = self.implied_probability_to_decimal(adjusted_prob)
        return suggested_odds
    
    def _calculate_maker_profit_margin(self, fair_odds: float, suggested_odds: float, commission: float) -> float:
        """Calculate expected profit margin for market making"""
        fair_prob = self.decimal_to_implied_probability(fair_odds)
        suggested_prob = self.decimal_to_implied_probability(suggested_odds)
        
        # Profit margin = (fair_prob / suggested_prob - 1) - commission
        if suggested_prob > 0:
            profit_margin = (fair_prob / suggested_prob - 1) - commission
            return profit_margin * 100  # Return as percentage
        
        return 0.0
    
    def _format_bet_description(self, market_key: str, outcome: Dict[str, Any], _event_data: Dict[str, Any]) -> str:
        """Format a human-readable bet description"""
        outcome_name = outcome.get('name', '')
        
        if market_key == 'h2h':
            return f"{outcome_name} to win"
        elif market_key == 'spreads':
            point = outcome.get('point', 0)
            if point > 0:
                return f"{outcome_name} +{point}"
            else:
                return f"{outcome_name} {point}"
        elif market_key == 'totals':
            point = outcome.get('point', 0)
            return f"{outcome_name} {point}"
        elif market_key.startswith('player_'):
            description = outcome.get('description', '')
            point = outcome.get('point', '')
            if point:
                return f"{description} {outcome_name} {point}"
            else:
                return f"{description} {outcome_name}"
        else:
            return f"{outcome_name} ({market_key})"
    
    def analyze_all_markets(self, odds_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze all markets for +EV opportunities and market making suggestions
        Returns dict with 'ev_opportunities' and 'market_making_suggestions'
        """
        all_ev_opportunities = []
        all_market_making_suggestions = []
        
        for sport_key, events in odds_data.items():
            logger.info(f"Analyzing {len(events)} events for {sport_key}")
            
            for event in events:
                # Find +EV opportunities
                ev_ops = self.find_ev_opportunities(event)
                all_ev_opportunities.extend(ev_ops)
                
                # Find market making suggestions
                mm_suggestions = self.suggest_market_making_odds(event)
                all_market_making_suggestions.extend(mm_suggestions)
        
        logger.info(f"Found {len(all_ev_opportunities)} +EV opportunities")
        logger.info(f"Generated {len(all_market_making_suggestions)} market making suggestions")
        
        return {
            'ev_opportunities': all_ev_opportunities,
            'market_making_suggestions': all_market_making_suggestions
        } 
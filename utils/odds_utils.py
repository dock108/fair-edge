"""
Odds conversion and classification utilities
Consolidates common odds manipulation functions used across the application
"""

from typing import Union


def american_to_decimal(odds_str: str) -> float:
    """
    Convert American odds to decimal odds
    
    Args:
        odds_str: American odds string (e.g., '+150', '-110')
    
    Returns:
        Decimal odds (e.g., 2.5, 1.91)
    
    Examples:
        >>> american_to_decimal('+150')
        2.5
        >>> american_to_decimal('-110')
        1.909
    """
    try:
        # Clean the odds string - remove parenthetical info and exchange adjustments
        odds_str = odds_str.split('(')[0].strip()
        odds_str = odds_str.split('→')[0].strip()
        
        if odds_str.startswith('+'):
            american = int(odds_str[1:])
            return (american / 100) + 1
        elif odds_str.startswith('-'):
            american = int(odds_str[1:])
            return (100 / american) + 1
        else:
            american = int(odds_str)
            if american > 0:
                return (american / 100) + 1
            else:
                return (100 / abs(american)) + 1
    except (ValueError, ZeroDivisionError):
        return 2.0  # Default to even odds


def decimal_to_american(decimal_odds: float) -> str:
    """
    Convert decimal odds to American odds format
    
    Args:
        decimal_odds: Decimal odds (e.g., 2.5, 1.91)
    
    Returns:
        American odds string (e.g., '+150', '-110')
    """
    if decimal_odds >= 2.0:
        american = int((decimal_odds - 1) * 100)
        return f"+{american}"
    else:
        american = int(100 / (decimal_odds - 1))
        return f"-{american}"


def calculate_implied_probability(decimal_odds: float) -> float:
    """
    Calculate implied probability from decimal odds
    
    Args:
        decimal_odds: Decimal odds
        
    Returns:
        Implied probability as percentage (0-100)
    """
    if decimal_odds <= 1:
        return 0.0
    return (1 / decimal_odds) * 100


def classify_ev_percentage(ev_percentage: float) -> str:
    """
    Classify expected value percentage into tiers
    
    Args:
        ev_percentage: EV as percentage (e.g., 4.5 for 4.5%)
        
    Returns:
        Classification string: 'excellent', 'high', 'positive', or 'neutral'
    """
    if ev_percentage >= 4.5:
        return "excellent"
    elif ev_percentage >= 2.5:
        return "high"
    elif ev_percentage > 0:
        return "positive"
    else:
        return "neutral"


def format_odds_display(odds_value: Union[str, float], format_type: str = "american") -> str:
    """
    Format odds for display with consistent styling
    
    Args:
        odds_value: Raw odds value
        format_type: 'american', 'decimal', or 'fractional'
        
    Returns:
        Formatted odds string
    """
    if odds_value == 'N/A' or odds_value is None:
        return 'N/A'
    
    if format_type == "american":
        if isinstance(odds_value, str):
            return odds_value
        else:
            return decimal_to_american(float(odds_value))
    elif format_type == "decimal":
        if isinstance(odds_value, str):
            return f"{american_to_decimal(odds_value):.2f}"
        else:
            return f"{float(odds_value):.2f}"
    else:
        # Default to returning as-is
        return str(odds_value)


def calculate_potential_payout(stake: float, decimal_odds: float) -> float:
    """
    Calculate potential payout (including stake) for a bet
    
    Args:
        stake: Bet amount
        decimal_odds: Odds in decimal format
        
    Returns:
        Total potential payout including original stake
    """
    return stake * decimal_odds


def calculate_potential_profit(stake: float, decimal_odds: float) -> float:
    """
    Calculate potential profit (excluding stake) for a bet
    
    Args:
        stake: Bet amount  
        decimal_odds: Odds in decimal format
        
    Returns:
        Potential profit excluding original stake
    """
    return stake * (decimal_odds - 1)


def compare_odds_value(odds1: str, odds2: str) -> int:
    """
    Compare two odds values to determine which is better for a bettor
    
    Args:
        odds1: First odds string in American format
        odds2: Second odds string in American format
        
    Returns:
        1 if odds1 is better, -1 if odds2 is better, 0 if equal
    """
    try:
        decimal1 = american_to_decimal(odds1)
        decimal2 = american_to_decimal(odds2)
        
        if decimal1 > decimal2:
            return 1
        elif decimal2 > decimal1:
            return -1
        else:
            return 0
    except (ValueError, TypeError):
        return 0 
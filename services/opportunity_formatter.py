"""
Opportunity formatter to transform backend data to frontend expected format
"""
import logging

logger = logging.getLogger(__name__)


def format_opportunity(opp):
    """Format a single opportunity to match frontend expected structure"""
    # Parse available odds from string format
    available_odds = []
    if isinstance(opp.get("All Available Odds"), str):
        odds_parts = opp.get("All Available Odds", "").split(";")
        for part in odds_parts:
            if ":" in part:
                bookmaker, odds = part.strip().split(":", 1)
                available_odds.append({"bookmaker": bookmaker.strip(), "odds": odds.strip()})

    # Extract EV percentage value
    ev_raw = opp.get("EV_Raw", 0)
    ev_percentage = ev_raw * 100 if isinstance(ev_raw, (int, float)) else 0

    # Determine EV classification
    if ev_percentage >= 2:
        ev_classification = "high"
    elif ev_percentage >= 0:
        ev_classification = "positive"
    else:
        ev_classification = "neutral"

    # Extract action link
    action_link = ""
    if opp.get("Links"):
        link_parts = opp["Links"].split("|")
        if link_parts:
            action_link = link_parts[0].replace("Take:", "").strip()

    # Improve description for period-specific bets
    bet_description = opp.get("Bet Description", "")
    market = opp.get("Market", "")

    # Add period context to description if missing
    if market and ("_1st_5" in market or "_h1" in market or "_q1" in market or "_p1" in market):
        if market.endswith("_1st_5_innings") or market.endswith("_1st_5"):
            if "first 5" not in bet_description.lower() and "1st 5" not in bet_description.lower():
                bet_description += " (First 5 Innings)"
        elif market.endswith("_h1"):
            if (
                "first half" not in bet_description.lower()
                and "1st half" not in bet_description.lower()
            ):
                bet_description += " (First Half)"
        elif market.endswith("_q1"):
            if (
                "first quarter" not in bet_description.lower()
                and "1st quarter" not in bet_description.lower()
            ):
                bet_description += " (First Quarter)"
        elif market.endswith("_p1"):
            if (
                "first period" not in bet_description.lower()
                and "1st period" not in bet_description.lower()
            ):
                bet_description += " (First Period)"

    return {
        "event": opp.get("Event", ""),
        "bet_description": bet_description,
        "bet_type": market,
        "ev_percentage": ev_percentage,
        "ev_classification": ev_classification,
        "available_odds": available_odds,
        "fair_odds": opp.get("Fair Odds", ""),
        "best_available_odds": opp.get("Best Available Odds", ""),
        "best_odds_source": opp.get("Best_Odds_Source", ""),
        "recommended_posting_odds": opp.get("Proposed Posting Odds", ""),
        "recommended_book": opp.get("Best_Odds_Source", ""),
        "action_link": action_link,
        "sport": opp.get("sport", ""),
        "_original": opp,  # For debugging
    }


def format_opportunities_for_frontend(opportunities, user_role="free", limit=None):
    """Format opportunities list for frontend consumption"""
    if not opportunities:
        return []

    # Transform each opportunity
    formatted = [format_opportunity(opp) for opp in opportunities]

    # Define main line markets (for basic users) - full game only
    main_line_markets = {
        "h2h",
        "spreads",
        "totals",
        "spread",
        "total",
        "point_spread",
        "over_under",
        "money_line",
    }

    # Period-specific markets are considered premium features
    period_specific_markets = {
        "h2h_1st_5_innings",
        "h2h_h1",
        "h2h_h2",
        "h2h_q1",
        "h2h_q2",
        "h2h_q3",
        "h2h_q4",
        "h2h_p1",
        "h2h_p2",
        "h2h_p3",
        "spreads_1st_5_innings",
        "spreads_h1",
        "spreads_h2",
        "spreads_q1",
        "spreads_q2",
        "spreads_q3",
        "spreads_q4",
        "totals_1st_5_innings",
        "totals_h1",
        "totals_h2",
        "totals_q1",
        "totals_q2",
        "totals_q3",
        "totals_q4",
    }

    # Apply role-based filtering
    if user_role in ["free", "anonymous", None]:
        # Free/unauthenticated users: Sort by EV and limit to 10 worst opportunities
        logger.info(f"Applying free user restrictions: limiting to 10 worst opportunities")
        formatted.sort(key=lambda x: x["ev_percentage"])
        formatted = formatted[:10] if len(formatted) > 10 else formatted
    elif user_role == "basic":
        # Basic users: Only full-game main lines (no period-specific or player props)
        original_count = len(formatted)

        # Filter to main lines only, excluding period-specific markets
        main_line_opportunities = [
            opp
            for opp in formatted
            if opp["bet_type"] in main_line_markets
            and opp["bet_type"] not in period_specific_markets
        ]

        if main_line_opportunities:
            # Show only full-game main lines
            formatted = main_line_opportunities
            logger.info(
                f"Basic user filter: {original_count} -> {len(formatted)} opportunities (full-game main lines only)"
            )
        else:
            # Show player props as fallback if no main lines available
            logger.info(
                f"Basic user filter: No full-game main lines available, showing {len(formatted)} opportunities as fallback"
            )
            logger.info(
                "Note: Basic plan normally includes only full-game main lines (moneyline, spreads, totals)"
            )
            logger.info(
                "Period-specific markets (1st 5 innings, quarters, etc.) require Premium subscription"
            )
    # Premium, admin users see everything (no filtering)

    # Apply limit if specified
    if limit and len(formatted) > limit:
        formatted = formatted[:limit]

    logger.info(f"Formatted {len(formatted)} opportunities for role {user_role}")
    return formatted

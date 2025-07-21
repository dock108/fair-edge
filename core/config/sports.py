"""
Sports and bookmaker configuration consolidated from services/config.py
"""
from typing import Any, Dict, List


class SportsConfig:
    """Sports, bookmakers, and markets configuration"""

    # Bookmaker configuration - only the 5 specified platforms
    BOOKMAKERS = {
        "pinnacle": {
            "key": "pinnacle",
            "name": "Pinnacle",
            "type": "sharp",
            "region": "eu",
            "affiliate_url": "https://pinnacle.com",
        },
        "draftkings": {
            "key": "draftkings",
            "name": "DraftKings",
            "type": "us_book",
            "region": "us",
            "affiliate_url": "https://draftkings.com",
        },
        "fanduel": {
            "key": "fanduel",
            "name": "FanDuel",
            "type": "us_book",
            "region": "us",
            "affiliate_url": "https://fanduel.com",
        },
        "novig": {
            "key": "novig",
            "name": "Novig",
            "type": "exchange",
            "region": "us_ex",
            "affiliate_url": "https://novig.com",
        },
        "prophetx": {
            "key": "prophetx",
            "name": "ProphetX",
            "type": "exchange",
            "region": "us_ex",
            "affiliate_url": "https://prophetx.com",
        },
    }

    # Featured markets (available on main /sports/{sport}/odds endpoint)
    FEATURED_MARKETS = ["h2h", "spreads", "totals"]

    # Additional markets (require /events/{eventId}/odds endpoint)
    ADDITIONAL_MARKETS = {
        "americanfootball_nfl": [
            # Core passing props
            "player_pass_yds",
            "player_pass_tds",
            "player_pass_completions",
            "player_pass_attempts",
            "player_pass_interceptions",
            "player_pass_longest_completion",
            # Core rushing props
            "player_rush_yds",
            "player_rush_tds",
            "player_rush_attempts",
            "player_rush_longest",
            # Core receiving props
            "player_reception_yds",
            "player_reception_tds",
            "player_receptions",
            "player_reception_longest",
            # Combo props
            "player_pass_rush_reception_yds",
            "player_pass_rush_reception_tds",
            "player_rush_reception_yds",
            "player_rush_reception_tds",
            # Touchdown scorer markets
            "player_anytime_td",
            "player_1st_td",
            "player_last_td",
            # Defense props
            "player_sacks",
            "player_tackles_assists",
            "player_defensive_interceptions",
            # Kicking props
            "player_field_goals",
            "player_kicking_points",
            # Additional markets
            "alternate_spreads",
            "alternate_totals",
            "team_totals",
            # Period markets
            "h2h_h1",
            "h2h_h2",
            "spreads_h1",
            "spreads_h2",
            "totals_h1",
            "totals_h2",
            "h2h_q1",
            "spreads_q1",
            "totals_q1",
        ],
        "basketball_nba": [
            # Core scoring props
            "player_points",
            "player_points_q1",
            "player_field_goals",
            "player_threes",
            "player_frees_made",
            # Core stat props
            "player_rebounds",
            "player_assists",
            "player_steals",
            "player_blocks",
            "player_turnovers",
            # Combo props
            "player_points_rebounds_assists",
            "player_points_rebounds",
            "player_points_assists",
            "player_rebounds_assists",
            "player_blocks_steals",
            # Special markets
            "player_double_double",
            "player_triple_double",
            "player_first_basket",
            "player_first_team_basket",
            # Additional markets
            "alternate_spreads",
            "alternate_totals",
            "team_totals",
            # Period markets
            "h2h_h1",
            "h2h_h2",
            "spreads_h1",
            "spreads_h2",
            "totals_h1",
            "totals_h2",
            "h2h_q1",
            "h2h_q4",
            "spreads_q1",
            "spreads_q4",
            "totals_q1",
            "totals_q4",
        ],
        "basketball_ncaab": [
            "player_points",
            "player_rebounds",
            "player_assists",
            "player_threes",
            "player_steals",
            "player_blocks",
            "player_points_rebounds_assists",
            "player_points_rebounds",
            "player_points_assists",
            "player_double_double",
            "player_first_basket",
            "alternate_spreads",
            "alternate_totals",
            "team_totals",
            "h2h_h1",
            "h2h_h2",
            "spreads_h1",
            "spreads_h2",
            "totals_h1",
            "totals_h2",
        ],
        "baseball_mlb": [
            # Core batter props
            "batter_home_runs",
            "batter_hits",
            "batter_total_bases",
            "batter_rbis",
            "batter_runs_scored",
            "batter_singles",
            "batter_doubles",
            "batter_triples",
            "batter_walks",
            "batter_strikeouts",
            "batter_stolen_bases",
            "batter_hits_runs_rbis",
            "batter_first_home_run",
            # Core pitcher props
            "pitcher_strikeouts",
            "pitcher_hits_allowed",
            "pitcher_walks",
            "pitcher_earned_runs",
            "pitcher_outs",
            "pitcher_record_a_win",
            # Alternate props
            "batter_total_bases_alternate",
            "batter_home_runs_alternate",
            "batter_hits_alternate",
            "batter_rbis_alternate",
            "pitcher_hits_allowed_alternate",
            "pitcher_walks_alternate",
            "pitcher_strikeouts_alternate",
            # Additional markets
            "alternate_spreads",
            "alternate_totals",
            "team_totals",
            # Period markets
            "h2h_1st_5_innings",
            "spreads_1st_5_innings",
            "totals_1st_5_innings",
            "h2h_1st_3_innings",
            "totals_1st_3_innings",
        ],
        "icehockey_nhl": [
            # Core player props
            "player_points",
            "player_goals",
            "player_assists",
            "player_shots_on_goal",
            "player_blocked_shots",
            "player_power_play_points",
            "player_total_saves",
            # Goal scorer markets
            "player_goal_scorer_anytime",
            "player_goal_scorer_first",
            "player_goal_scorer_last",
            # Additional markets
            "alternate_spreads",
            "alternate_totals",
            "team_totals",
            # Period markets
            "h2h_p1",
            "h2h_p2",
            "h2h_p3",
            "spreads_p1",
            "spreads_p2",
            "spreads_p3",
            "totals_p1",
            "totals_p2",
            "totals_p3",
        ],
    }

    # Sports to monitor
    SUPPORTED_SPORTS = [
        "americanfootball_nfl",
        "basketball_nba",
        "basketball_ncaab",
        "baseball_mlb",
        "icehockey_nhl",
        "soccer_epl",
        "soccer_uefa_champs_league",
    ]

    # Exchange commission rates (for market making calculations)
    EXCHANGE_COMMISSIONS = {
        "novig": 0.02,  # 2% commission
        "prophetx": 0.025,  # 2.5% commission (estimate)
    }

    # Maker edge margin (additional profit margin for market making)
    MAKER_EDGE_MARGIN = 0.01  # 1% additional edge

    # Major books for market validation
    MAJOR_BOOKS = ["pinnacle", "draftkings", "fanduel"]

    # Exchange platforms
    EXCHANGES = ["novig", "prophetx"]

    # All supported bookmakers
    ALL_BOOKMAKERS = MAJOR_BOOKS + EXCHANGES

    @property
    def default_markets(self) -> List[str]:
        """Legacy compatibility property"""
        return self.FEATURED_MARKETS

    @property
    def markets(self) -> List[str]:
        """Legacy compatibility property"""
        return self.FEATURED_MARKETS

    def get_bookmaker_config(self, bookmaker_key: str) -> Dict[str, Any]:
        """Get configuration for a specific bookmaker"""
        return self.BOOKMAKERS.get(bookmaker_key, {})

    def get_sport_markets(self, sport: str) -> List[str]:
        """Get additional markets for a specific sport"""
        return self.ADDITIONAL_MARKETS.get(sport, [])

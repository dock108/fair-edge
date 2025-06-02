"""
Application constants for role-based access control and premium features
"""

# Fields to mask/remove for free users (advanced analytics)
MASK_FIELDS_FOR_FREE = (
    "kelly_factor", 
    "true_hold", 
    "confidence_score",
    "historical_performance",
    "risk_assessment",
    "recommended_stake",
    "expected_roi",
    "market_efficiency",
    "sharp_money_indicator"
)

# Premium features by role
ROLE_FEATURES = {
    "free": {
        "markets": "main_lines_only",  # h2h, spreads, totals only
        "analytics_depth": "basic",
        "refresh_rate_minutes": 30,
        "export_enabled": False,
        "alert_notifications": False,
        "custom_filters": True,  # Allow search/sport filtering
        "api_rate_limit": "30/minute"
    },
    "subscriber": {
        "markets": "all",  # All markets available
        "analytics_depth": "advanced", 
        "refresh_rate_minutes": 5,
        "export_enabled": True,
        "alert_notifications": True,
        "custom_filters": True,
        "api_rate_limit": "120/minute"
    },
    "admin": {
        "markets": "all",  # All markets available
        "analytics_depth": "full",
        "refresh_rate_minutes": 1,
        "export_enabled": True,
        "alert_notifications": True,
        "custom_filters": True,
        "api_rate_limit": "unlimited"
    }
}

# Cache keys for role-based data
CACHE_KEYS = {
    "ev_data_free": "ev_opportunities:free",
    "ev_data_full": "ev_opportunities:full", 
    "analytics_free": "analytics:free",
    "analytics_full": "analytics:full"
} 
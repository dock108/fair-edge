"""
Feature and role-based configuration consolidated from core/constants.py
"""
from typing import Dict, Any, Tuple


class FeatureConfig:
    """Role-based features and access control configuration"""
    
    # Fields to mask/remove for free users (advanced analytics)
    MASK_FIELDS_FOR_FREE: Tuple[str, ...] = (
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
    ROLE_FEATURES: Dict[str, Dict[str, Any]] = {
        "free": {
            "markets": "main_lines_only",  # h2h, spreads, totals only, ≤ -2% EV
            "analytics_depth": "basic",
            "refresh_rate_minutes": 5,  # Same refresh rate for all users
            "export_enabled": False,
            "alert_notifications": False,
            "custom_filters": False,  # No search/sport filtering for free users
            "api_rate_limit": "30/minute",
            "max_opportunities": 10,  # Limited to 10 sample opportunities
            "ev_threshold": -2.0  # Only show -2% EV or worse
        },
        "basic": {
            "markets": "main_lines_only",  # h2h, spreads, totals only
            "analytics_depth": "basic",
            "refresh_rate_minutes": 5,
            "export_enabled": False,
            "alert_notifications": False,
            "custom_filters": True,  # Allow search/sport filtering
            "api_rate_limit": "60/minute",
            "max_opportunities": None,  # Unlimited main line opportunities
            "ev_threshold": -999.0  # All EV values (using large negative number instead of -inf)
        },
        "premium": {
            "markets": "all",  # All markets available
            "analytics_depth": "advanced", 
            "refresh_rate_minutes": 5,
            "export_enabled": True,
            "alert_notifications": True,
            "custom_filters": True,
            "api_rate_limit": "120/minute",
            "max_opportunities": None,  # Unlimited opportunities
            "ev_threshold": -999.0  # All EV values (using large negative number instead of -inf)
        },
        # Keep subscriber for backward compatibility, map to premium
        "subscriber": {
            "markets": "all",  # All markets available
            "analytics_depth": "advanced", 
            "refresh_rate_minutes": 5,
            "export_enabled": True,
            "alert_notifications": True,
            "custom_filters": True,
            "api_rate_limit": "120/minute",
            "max_opportunities": None,  # Unlimited opportunities
            "ev_threshold": -999.0  # All EV values (using large negative number instead of -inf)
        },
        "admin": {
            "markets": "all",  # All markets available
            "analytics_depth": "full",
            "refresh_rate_minutes": 1,
            "export_enabled": True,
            "alert_notifications": True,
            "custom_filters": True,
            "api_rate_limit": "unlimited",
            "max_opportunities": None,  # Unlimited opportunities
            "ev_threshold": -999.0  # All EV values (using large negative number instead of -inf)
        }
    }

    def get_user_features(self, role: str) -> Dict[str, Any]:
        """Get features available for a specific user role"""
        return self.ROLE_FEATURES.get(role, self.ROLE_FEATURES["free"])
    
    def has_feature(self, role: str, feature: str) -> bool:
        """Check if a role has access to a specific feature"""
        features = self.get_user_features(role)
        return features.get(feature, False)
    
    def get_rate_limit(self, role: str) -> str:
        """Get API rate limit for a specific role"""
        features = self.get_user_features(role)
        return features.get("api_rate_limit", "30/minute")
    
    def should_mask_field(self, field_name: str, role: str) -> bool:
        """Check if a field should be masked for a specific role"""
        if role in ["basic", "premium", "subscriber", "admin"]:
            return False
        return field_name in self.MASK_FIELDS_FOR_FREE 
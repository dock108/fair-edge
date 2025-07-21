"""Sample data for testing Fair-Edge application."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import factory
from factory import Faker


class BettingOpportunityFactory(factory.Factory):
    """Factory for creating test betting opportunities."""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: f"opp_{n}")
    event = factory.LazyFunction(
        lambda: f"{Faker('company').generate()} vs {Faker('company').generate()}"
    )
    bet_desc = factory.Faker("sentence", nb_words=4)
    bet_type = factory.Faker(
        "random_element", elements=["moneyline", "spread", "total", "player_props"]
    )
    sport = factory.Faker("random_element", elements=["NFL", "NBA", "MLB", "NHL", "Soccer"])
    ev_pct = factory.Faker(
        "pyfloat",
        left_digits=2,
        right_digits=1,
        positive=True,
        min_value=1.0,
        max_value=25.0,
    )
    best_odds = factory.LazyAttribute(lambda obj: f"+{int(obj.ev_pct * 10)}")
    fair_odds = factory.LazyAttribute(lambda obj: f"+{int(obj.ev_pct * 8)}")
    best_source = factory.Faker(
        "random_element", elements=["DraftKings", "FanDuel", "BetMGM", "Caesars"]
    )
    game_time = factory.Faker("future_datetime", end_date="+30d")
    classification = factory.LazyAttribute(
        lambda obj: (
            "great"
            if obj.ev_pct >= 15
            else "good"
            if obj.ev_pct >= 10
            else "fair"
            if obj.ev_pct >= 5
            else "poor"
        )
    )


class UserFactory(factory.Factory):
    """Factory for creating test users."""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Faker("email")
    role = factory.Faker("random_element", elements=["free", "basic", "premium", "admin"])
    subscription_status = factory.LazyAttribute(
        lambda obj: "active" if obj.role in ["basic", "premium"] else "inactive"
    )
    device_id = factory.Faker("uuid4")
    apple_user_id = factory.Faker("uuid4")
    created_at = factory.Faker("past_datetime", start_date="-1y")
    last_login = factory.Faker("past_datetime", start_date="-30d")


class AppleReceiptFactory(factory.Factory):
    """Factory for creating test Apple receipt data."""

    class Meta:
        model = dict

    receipt_data = factory.Faker("sha256")
    product_id = factory.Faker(
        "random_element",
        elements=[
            "com.fairedge.basic_monthly",
            "com.fairedge.premium_monthly",
            "com.fairedge.premium_yearly",
        ],
    )
    transaction_id = factory.Sequence(lambda n: f"txn_{n}")
    original_transaction_id = factory.Sequence(lambda n: f"orig_txn_{n}")
    expires_date = factory.Faker("future_datetime", end_date="+1y")
    auto_renew_status = factory.Faker("random_element", elements=["0", "1"])
    purchase_date = factory.Faker("past_datetime", start_date="-30d")


# Sample data constants
SAMPLE_OPPORTUNITIES: List[Dict[str, Any]] = [
    {
        "id": "opp_1",
        "event": "Lakers vs Warriors",
        "bet_desc": "LeBron James Points Over 25.5",
        "bet_type": "player_props",
        "sport": "NBA",
        "ev_pct": 12.5,
        "best_odds": "+150",
        "fair_odds": "+120",
        "best_source": "DraftKings",
        "game_time": datetime.now() + timedelta(hours=2),
        "classification": "good",
    },
    {
        "id": "opp_2",
        "event": "Chiefs vs Bills",
        "bet_desc": "Kansas City Chiefs -3.5",
        "bet_type": "spread",
        "sport": "NFL",
        "ev_pct": 8.2,
        "best_odds": "-110",
        "fair_odds": "-105",
        "best_source": "FanDuel",
        "game_time": datetime.now() + timedelta(days=1),
        "classification": "fair",
    },
    {
        "id": "opp_3",
        "event": "Dodgers vs Padres",
        "bet_desc": "Total Runs Over 8.5",
        "bet_type": "total",
        "sport": "MLB",
        "ev_pct": 15.7,
        "best_odds": "+105",
        "fair_odds": "+85",
        "best_source": "BetMGM",
        "game_time": datetime.now() + timedelta(hours=6),
        "classification": "great",
    },
]

SAMPLE_USERS: List[Dict[str, Any]] = [
    {
        "id": "user_free",
        "email": "free@test.com",
        "role": "free",
        "subscription_status": "inactive",
        "device_id": "device_free_123",
        "apple_user_id": None,
    },
    {
        "id": "user_basic",
        "email": "basic@test.com",
        "role": "basic",
        "subscription_status": "active",
        "device_id": "device_basic_456",
        "apple_user_id": "apple_basic_789",
    },
    {
        "id": "user_premium",
        "email": "premium@test.com",
        "role": "premium",
        "subscription_status": "active",
        "device_id": "device_premium_789",
        "apple_user_id": "apple_premium_012",
    },
    {
        "id": "user_admin",
        "email": "admin@test.com",
        "role": "admin",
        "subscription_status": "active",
        "device_id": "device_admin_012",
        "apple_user_id": "apple_admin_345",
    },
]

SAMPLE_API_RESPONSES: Dict[str, Any] = {
    "odds_api_success": {
        "success": True,
        "data": [
            {
                "id": "game_123",
                "sport_key": "americanfootball_nfl",
                "sport_title": "NFL",
                "commence_time": "2025-01-20T18:00:00Z",
                "home_team": "Dallas Cowboys",
                "away_team": "Green Bay Packers",
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Dallas Cowboys", "price": 1.85},
                                    {"name": "Green Bay Packers", "price": 2.05},
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    },
    "apple_receipt_validation": {
        "status": 0,
        "receipt": {
            "receipt_type": "ProductionSandbox",
            "in_app": [
                {
                    "product_id": "com.fairedge.premium_monthly",
                    "transaction_id": "test_txn_123",
                    "original_transaction_id": "test_orig_123",
                    "expires_date_ms": "1740686400000",
                    "is_trial_period": "false",
                    "cancellation_date_ms": None,
                }
            ],
        },
    },
    "supabase_auth_success": {
        "user": {
            "id": "supabase_user_123",
            "email": "test@fair-edge.com",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "session": {
            "access_token": "supabase_jwt_token",
            "refresh_token": "supabase_refresh_token",
            "expires_in": 3600,
        },
    },
}

# Error response templates
ERROR_RESPONSES: Dict[str, Any] = {
    "odds_api_error": {"success": False, "error": "API rate limit exceeded"},
    "apple_receipt_invalid": {"status": 21002, "is-retryable": False},
    "supabase_auth_error": {"error": {"message": "Invalid login credentials", "status": 400}},
}

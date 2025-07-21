"""Mock HTTP responses for external API testing."""

import json
from typing import Any, Dict
from unittest.mock import MagicMock

import responses


class MockOddsAPI:
    """Mock responses for The Odds API."""

    @staticmethod
    def success_response():
        """Mock successful odds API response."""
        return {
            "success": True,
            "data": [
                {
                    "id": "nfl_game_123",
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
                                },
                                {
                                    "key": "spreads",
                                    "outcomes": [
                                        {
                                            "name": "Dallas Cowboys",
                                            "price": 1.91,
                                            "point": -3.5,
                                        },
                                        {
                                            "name": "Green Bay Packers",
                                            "price": 1.91,
                                            "point": 3.5,
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "key": "fanduel",
                            "title": "FanDuel",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Dallas Cowboys", "price": 1.83},
                                        {"name": "Green Bay Packers", "price": 2.10},
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def rate_limit_error():
        """Mock rate limit error response."""
        return {
            "success": False,
            "error": "Rate limit exceeded. Please try again later.",
        }

    @staticmethod
    def api_key_error():
        """Mock invalid API key error."""
        return {"success": False, "error": "Invalid API key"}


class MockAppleAPI:
    """Mock responses for Apple App Store API."""

    @staticmethod
    def valid_receipt_response():
        """Mock valid receipt validation response."""
        return {
            "status": 0,
            "environment": "Sandbox",
            "receipt": {
                "receipt_type": "ProductionSandbox",
                "bundle_id": "com.fairedge.app",
                "application_version": "1.0",
                "in_app": [
                    {
                        "product_id": "com.fairedge.premium_monthly",
                        "transaction_id": "test_transaction_123",
                        "original_transaction_id": "test_original_123",
                        "purchase_date_ms": "1705708800000",
                        "expires_date_ms": "1708387200000",
                        "is_trial_period": "false",
                        "cancellation_date_ms": None,
                        "auto_renew_status": "1",
                    }
                ],
            },
            "latest_receipt_info": [
                {
                    "product_id": "com.fairedge.premium_monthly",
                    "transaction_id": "test_transaction_123",
                    "original_transaction_id": "test_original_123",
                    "expires_date_ms": "1708387200000",
                    "auto_renew_status": "1",
                }
            ],
        }

    @staticmethod
    def invalid_receipt_response():
        """Mock invalid receipt response."""
        return {"status": 21002, "is-retryable": False, "environment": "Sandbox"}

    @staticmethod
    def expired_receipt_response():
        """Mock expired receipt response."""
        return {
            "status": 0,
            "environment": "Sandbox",
            "receipt": {
                "receipt_type": "ProductionSandbox",
                "bundle_id": "com.fairedge.app",
                "in_app": [
                    {
                        "product_id": "com.fairedge.premium_monthly",
                        "transaction_id": "test_transaction_456",
                        "expires_date_ms": "1704067200000",  # Expired date
                        "cancellation_date_ms": "1704067200000",
                    }
                ],
            },
        }


class MockSupabaseAPI:
    """Mock responses for Supabase API."""

    @staticmethod
    def auth_success_response():
        """Mock successful authentication response."""
        return {
            "user": {
                "id": "supabase_user_123",
                "email": "test@fair-edge.com",
                "phone": None,
                "created_at": "2025-01-01T00:00:00.000Z",
                "confirmed_at": "2025-01-01T00:00:00.000Z",
                "role": "authenticated",
                "app_metadata": {},
                "user_metadata": {},
            },
            "session": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": 1740686400,
                "refresh_token": "test_refresh_token",
                "user": {"id": "supabase_user_123", "email": "test@fair-edge.com"},
            },
        }

    @staticmethod
    def auth_error_response():
        """Mock authentication error response."""
        return {"error": {"message": "Invalid login credentials", "status": 400}}

    @staticmethod
    def user_info_response():
        """Mock user info response."""
        return {
            "id": "supabase_user_123",
            "email": "test@fair-edge.com",
            "role": "premium",
            "subscription_status": "active",
            "device_id": "test_device_123",
            "created_at": "2025-01-01T00:00:00.000Z",
        }


class MockRedisResponse:
    """Mock Redis client responses."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        """Mock Redis get operation."""
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        """Mock Redis set operation."""
        self.data[key] = value
        return True

    async def delete(self, key: str):
        """Mock Redis delete operation."""
        if key in self.data:
            del self.data[key]
            return 1
        return 0

    async def exists(self, key: str):
        """Mock Redis exists operation."""
        return 1 if key in self.data else 0

    async def expire(self, key: str, seconds: int):
        """Mock Redis expire operation."""
        return True if key in self.data else False


def setup_responses_mocks():
    """Set up responses library mocks for external APIs."""

    # Odds API mocks
    responses.add(
        responses.GET,
        "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds",
        json=MockOddsAPI.success_response(),
        status=200,
    )

    responses.add(
        responses.GET,
        "https://api.the-odds-api.com/v4/sports/basketball_nba/odds",
        json=MockOddsAPI.success_response(),
        status=200,
    )

    # Apple receipt validation mocks
    responses.add(
        responses.POST,
        "https://buy.itunes.apple.com/verifyReceipt",
        json=MockAppleAPI.valid_receipt_response(),
        status=200,
    )

    responses.add(
        responses.POST,
        "https://sandbox.itunes.apple.com/verifyReceipt",
        json=MockAppleAPI.valid_receipt_response(),
        status=200,
    )

    # Supabase auth mocks
    responses.add(
        responses.POST,
        "https://test.supabase.co/auth/v1/token",
        json=MockSupabaseAPI.auth_success_response(),
        status=200,
    )


# Utility functions for test setup
def create_mock_request(
    method: str = "GET", url: str = "/", headers: Dict = None, json_data: Dict = None
):
    """Create a mock FastAPI request object."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.url.path = url
    mock_request.headers = headers or {}
    mock_request.json = lambda: json_data or {}
    return mock_request


def create_auth_headers(user_id: str = "test_user_123", role: str = "premium") -> Dict[str, str]:
    """Create authentication headers for testing."""
    # In a real implementation, you'd create a proper JWT token
    # For testing, we'll use a simple format that your auth system can mock
    test_token = f"test_token_{user_id}_{role}"
    return {"Authorization": f"Bearer {test_token}"}


def assert_api_response_format(response_data: Dict[str, Any], expected_fields: list):
    """Assert that API response has expected format."""
    assert isinstance(response_data, dict)
    for field in expected_fields:
        assert field in response_data, f"Expected field '{field}' not found in response"


def assert_opportunity_format(opportunity: Dict[str, Any]):
    """Assert that opportunity data has correct format."""
    required_fields = [
        "id",
        "event",
        "bet_desc",
        "bet_type",
        "sport",
        "ev_pct",
        "best_odds",
        "fair_odds",
        "best_source",
        "game_time",
        "classification",
    ]
    assert_api_response_format(opportunity, required_fields)
    assert isinstance(opportunity["ev_pct"], (int, float))
    assert opportunity["ev_pct"] >= 0
    assert opportunity["classification"] in ["poor", "fair", "good", "great"]

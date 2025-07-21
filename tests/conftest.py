"""Pytest configuration and shared fixtures for Fair-Edge testing."""

import asyncio
import os
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables BEFORE importing app
os.environ.update(
    {
        "APP_ENV": "test",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "test_service_role_key",
        "SUPABASE_JWT_SECRET": "test_jwt_secret_that_is_long_enough_for_validation",
        "DB_CONNECTION_STRING": "postgresql://test_user:test_password@localhost:5432/test_db",
        "ODDS_API_KEY": "test_odds_api_key",
        "TESTING": "true",
    }
)

# Import your app and database components AFTER setting env vars
from app import app
from core.settings import get_settings
from db import get_db
from models import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings configuration."""
    return {
        "DATABASE_URL": "postgresql://test_user:test_password@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/1",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test_anon_key",
        "SUPABASE_JWT_SECRET": "test_jwt_secret_that_is_long_enough_for_validation",
        "THE_ODDS_API_KEY": "test_odds_api_key",
        "DEBUG_MODE": True,
        "APP_ENV": "test",
    }


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create test database engine."""
    engine = create_engine(test_settings["DATABASE_URL"].replace("+asyncpg", ""), echo=False)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_test_engine(test_settings):
    """Create async test database engine."""
    engine = create_async_engine(test_settings["DATABASE_URL"], echo=False)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(async_test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(db_session):
    """Create a test client with database session override."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.expire = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_odds_api():
    """Mock external odds API responses."""
    return {
        "success": True,
        "data": [
            {
                "id": "test_game_1",
                "sport_key": "americanfootball_nfl",
                "sport_title": "NFL",
                "commence_time": "2025-01-20T18:00:00Z",
                "home_team": "New York Giants",
                "away_team": "Philadelphia Eagles",
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "New York Giants", "price": 2.50},
                                    {"name": "Philadelphia Eagles", "price": 1.65},
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test_user_123",
        "email": "test@fair-edge.com",
        "role": "premium",
        "subscription_status": "active",
        "device_id": "test_device_123",
        "apple_user_id": "test_apple_user",
    }


@pytest.fixture
def sample_opportunity_data():
    """Sample betting opportunity data for testing."""
    return {
        "id": "opp_123",
        "event": "Lakers vs Warriors",
        "bet_desc": "LeBron Points Over 25.5",
        "bet_type": "player_props",
        "sport": "NBA",
        "ev_pct": 12.5,
        "best_odds": "+150",
        "fair_odds": "+120",
        "best_source": "DraftKings",
        "game_time": "2025-01-20 20:00:00",
        "classification": "great",
    }


@pytest.fixture
def jwt_token():
    """Sample JWT token for testing authentication."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiZW1haWwiOiJ0ZXN0QGZhaXItZWRnZS5jb20iLCJyb2xlIjoicHJlbWl1bSJ9.test_signature"


@pytest.fixture
def auth_headers(jwt_token):
    """Authentication headers for API testing."""
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password = AsyncMock(
        return_value=MagicMock(user=MagicMock(id="test_user_123"))
    )
    mock_client.auth.get_user = AsyncMock(
        return_value=MagicMock(user=MagicMock(id="test_user_123"))
    )
    return mock_client


@pytest.fixture
def mock_apple_receipt():
    """Mock Apple receipt data for IAP testing."""
    return {
        "receipt_data": "base64_encoded_receipt_data",
        "product_id": "com.fairedge.premium_monthly",
        "transaction_id": "test_transaction_123",
        "original_transaction_id": "test_original_123",
        "expires_date": "2025-02-20 12:00:00",
        "auto_renew_status": "1",
    }


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "database: mark test as requiring database")

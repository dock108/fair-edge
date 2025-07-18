"""
Database models for bet-intel application
Implements persistent storage for betting opportunities with normalized schema
"""
from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Integer,
    Index, func, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum
import hashlib
import json
from typing import Dict, Any

Base = declarative_base()


# Explicit Enum definitions for better data integrity
class BookType(str, Enum):
    """Sportsbook types"""
    US_BOOK = "us_book"
    EXCHANGE = "exchange"
    SHARP = "sharp"
    OFFSHORE = "offshore"


class Region(str, Enum):
    """Geographic regions"""
    US = "us"
    EU = "eu"
    UK = "uk"
    AU = "au"
    GLOBAL = "global"


class UserRole(str, Enum):
    """User role types"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ADMIN = "admin"


class SubscriptionStatus(str, Enum):
    """Subscription status types"""
    NONE = "none"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class VolumeIndicator(str, Enum):
    """Volume indicators for bet offers"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Sport(Base):
    """Lookup table for sports"""
    __tablename__ = "sports"
    
    sport_id = Column(String(50), primary_key=True)  # e.g., "americanfootball_nfl"
    name = Column(String(100), nullable=False)  # e.g., "NFL"
    category = Column(String(50))  # e.g., "americanfootball"
    
    # Relationships
    bets = relationship("Bet", back_populates="sport_ref")


class League(Base):
    """Lookup table for leagues/competitions"""
    __tablename__ = "leagues"
    
    league_id = Column(String(50), primary_key=True)  # e.g., "nfl", "nba"
    name = Column(String(100), nullable=False)  # e.g., "National Football League"
    sport_id = Column(String(50), ForeignKey("sports.sport_id"))
    
    # Relationships
    sport = relationship("Sport")
    bets = relationship("Bet", back_populates="league_ref")


class Book(Base):
    """Lookup table for sportsbooks"""
    __tablename__ = "books"
    
    book_id = Column(String(50), primary_key=True)  # e.g., "draftkings", "fanduel"
    name = Column(String(100), nullable=False)  # e.g., "DraftKings"
    book_type = Column(
        SAEnum(BookType, name="book_type_enum", create_constraint=True),
        default=BookType.US_BOOK
    )
    region = Column(
        SAEnum(Region, name="region_enum", create_constraint=True),
        default=Region.US
    )
    affiliate_url = Column(Text)
    active = Column(Boolean, default=True)
    
    # Note: No direct relationship to BetOffer since we aggregate odds by bet_id


class Bet(Base):
    """Static metadata for betting opportunities"""
    __tablename__ = "bets"
    
    # Primary key - deterministic hash of bet attributes
    bet_id = Column(String(64), primary_key=True)  # SHA-256 hash (64 chars)
    
    # Core identifiers
    sport = Column(String(50), ForeignKey("sports.sport_id"), nullable=False)
    league = Column(String(50), ForeignKey("leagues.league_id"))
    
    # Event details
    event_name = Column(Text, nullable=False)  # Full event description
    home_team = Column(String(100))  # For team sports
    away_team = Column(String(100))  # For team sports
    player_name = Column(String(100))  # For player props
    
    # Bet type and market
    bet_type = Column(String(100), nullable=False)  # e.g., "h2h", "spreads", "player_points"
    market_description = Column(Text)  # Human-readable description
    
    # Bet parameters (stored as JSON for flexibility)
    parameters = Column(JSON)  # e.g., {"spread": -3.5, "total": 42.5}
    
    # Outcome side (for one-sided bets)
    outcome_side = Column(String(50))  # e.g., "over", "under", "home", "away"
    
    # Event timing
    event_time = Column(DateTime)  # When the event starts/occurs
    
    # Deduplication key
    sha_key = Column(String(64))  # SHA hash for deduplication
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sport_ref = relationship("Sport", back_populates="bets")
    league_ref = relationship("League", back_populates="bets")
    offers = relationship("BetOffer", back_populates="bet_ref", cascade="all, delete-orphan")
    
    # Indexes for performance and composite unique constraint for deduplication
    __table_args__ = (
        Index('idx_bets_sport_league', 'sport', 'league'),
        Index('idx_bets_bet_type', 'bet_type'),
        Index('idx_bets_teams', 'home_team', 'away_team'),
        Index('idx_bets_created_at', 'created_at'),
        UniqueConstraint(
            "sport", "league", "bet_type",
            "event_time", "sha_key",
            name="uq_bet_dedup"
        ),
    )
    
    @staticmethod
    def generate_bet_id(sport: str, league: str, event_name: str, bet_type: str, 
                        parameters: Dict[str, Any], outcome_side: str = None) -> str:
        """
        Generate deterministic hash-based bet_id from key attributes
        
        Args:
            sport: Sport identifier (e.g., "americanfootball_nfl")
            league: League identifier (e.g., "nfl")
            event_name: Full event name/description
            bet_type: Market type (e.g., "h2h", "spreads")
            parameters: Bet parameters dict (e.g., {"spread": -3.5})
            outcome_side: Side of the bet if applicable
            
        Returns:
            64-character SHA-256 hash string
        """
        # Normalize parameters for consistent hashing
        normalized_params = json.dumps(parameters or {}, sort_keys=True)
        
        # Create hash input string
        hash_input = "|".join([
            str(sport or ""),
            str(league or ""),
            str(event_name or ""),
            str(bet_type or ""),
            normalized_params,
            str(outcome_side or "")
        ])
        
        # Generate SHA-256 hash
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    @classmethod
    def create_or_get_bet_id(cls, opportunity_data: Dict[str, Any]) -> str:
        """
        Generate bet_id from opportunity data structure
        
        Args:
            opportunity_data: Dict containing bet opportunity info
            
        Returns:
            Generated bet_id hash
        """
        # Extract key fields from opportunity data
        sport = opportunity_data.get('sport', '')
        league = opportunity_data.get('league', '')
        event_name = opportunity_data.get('Event', opportunity_data.get('event', ''))
        bet_type = opportunity_data.get('Market', opportunity_data.get('bet_type', ''))
        
        # Extract parameters from description or other fields
        parameters = {}
        bet_description = opportunity_data.get('Bet Description', opportunity_data.get('bet_description', ''))
        
        # Parse common parameters from description
        if 'spread' in bet_description.lower() or bet_type in ['spreads']:
            # Try to extract spread value
            import re
            spread_match = re.search(r'[+-]?\d+\.?\d*', bet_description)
            if spread_match:
                parameters['spread'] = float(spread_match.group())
        
        if 'total' in bet_description.lower() or 'over' in bet_description.lower() or 'under' in bet_description.lower():
            # Try to extract total value
            import re
            total_match = re.search(r'\d+\.?\d*', bet_description)
            if total_match:
                parameters['total'] = float(total_match.group())
        
        # Determine outcome side
        outcome_side = None
        if 'over' in bet_description.lower():
            outcome_side = 'over'
        elif 'under' in bet_description.lower():
            outcome_side = 'under'
        elif 'home' in bet_description.lower():
            outcome_side = 'home'
        elif 'away' in bet_description.lower():
            outcome_side = 'away'
        
        return cls.generate_bet_id(sport, league, event_name, bet_type, parameters, outcome_side)


class BetOffer(Base):
    """Aggregated odds data for betting opportunities across all supported books"""
    __tablename__ = "bet_offers"
    
    # Primary key
    offer_id = Column(String(36), primary_key=True)  # UUID
    
    # Foreign key to static bet data
    bet_id = Column(String(64), ForeignKey("bets.bet_id"), nullable=False)
    
    # Odds columns for each of the 5 supported books (JSON format)
    draftkings_odds = Column(JSON)  # e.g., {"american": "+110", "decimal": 2.10, "ev": 0.05}
    fanduel_odds = Column(JSON)     # e.g., {"american": "+105", "decimal": 2.05, "ev": 0.03}
    novig_odds = Column(JSON)       # e.g., {"american": "+115", "decimal": 2.15, "ev": 0.07}
    prophetx_odds = Column(JSON)    # e.g., {"american": "+120", "decimal": 2.20, "ev": 0.08}
    pinnacle_odds = Column(JSON)    # e.g., {"american": "+108", "decimal": 2.08, "ev": 0.04}
    
    # Aggregated metrics across all books
    best_odds = Column(JSON)        # Best odds found across all books
    best_expected_value = Column(Float)  # Highest EV found
    best_book = Column(String(50))  # Which book has the best odds
    books_count = Column(Integer, default=0)  # How many books have this bet
    
    # Fair odds and market analysis
    fair_odds = Column(JSON)  # Fair odds calculation
    market_average = Column(JSON)  # Average odds across available books
    
    # Quality metrics
    confidence_score = Column(Float)  # Confidence in this data point
    volume_indicator = Column(
        SAEnum(VolumeIndicator, name="volume_indicator_enum", create_constraint=True),
        default=VolumeIndicator.UNKNOWN
    )
    
    # Additional offer data
    offer_metadata = Column(JSON)  # Any additional aggregated data
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    refresh_cycle_id = Column(String(36))  # ID linking offers from same refresh
    
    # Relationships
    bet_ref = relationship("Bet", back_populates="offers")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_bet_offers_bet_id', 'bet_id'),
        Index('idx_bet_offers_timestamp', 'timestamp'),
        Index('idx_bet_offers_best_ev', 'best_expected_value'),
        Index('idx_bet_offers_best_book', 'best_book'),
        Index('idx_bet_offers_bet_timestamp', 'bet_id', 'timestamp'),
        Index('idx_bet_offers_refresh_cycle', 'refresh_cycle_id'),
        Index('idx_bet_offers_books_count', 'books_count'),
    )
    
    @staticmethod
    def generate_offer_id() -> str:
        """Generate unique offer_id using UUID"""
        import uuid
        return str(uuid.uuid4())


# Additional indexes for common query patterns
Index('idx_bets_sport_type_created', Bet.sport, Bet.bet_type, Bet.created_at)
Index('idx_offers_recent_high_ev', BetOffer.timestamp, BetOffer.best_expected_value)


# User profiles table (enhance existing if needed)
class UserProfile(Base):
    """Enhanced user profiles for analytics features"""
    __tablename__ = "profiles"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    role = Column(
        SAEnum(UserRole, name="user_role_enum", create_constraint=True),
        default=UserRole.FREE
    )
    subscription_status = Column(
        SAEnum(SubscriptionStatus, name="subscription_status_enum", create_constraint=True),
        default=SubscriptionStatus.NONE
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Analytics preferences
    preferred_sports = Column(JSON)  # List of preferred sports
    alert_thresholds = Column(JSON)  # EV thresholds for alerts
    analytics_settings = Column(JSON)  # User analytics preferences
    
    # Apple In-App Purchase fields
    apple_transaction_id = Column(String(255))  # Current App Store transaction ID
    apple_original_transaction_id = Column(String(255))  # Original transaction ID for subscription group
    apple_receipt_data = Column(Text)  # Latest receipt data from App Store
    apple_subscription_group_id = Column(String(255))  # Apple subscription group identifier
    apple_purchase_date = Column(DateTime(timezone=True))  # Date of purchase/subscription start
    apple_expires_date = Column(DateTime(timezone=True))  # Subscription expiration date
    
    # Stripe fields for web users (maintaining compatibility)
    stripe_customer_id = Column(String(255))  # Stripe customer ID
    stripe_subscription_id = Column(String(255))  # Stripe subscription ID


class DeviceToken(Base):
    """Device tokens for push notifications"""
    __tablename__ = "device_tokens"
    
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    device_token = Column(String(255), unique=True, nullable=False)
    device_type = Column(String(10), nullable=False)  # "ios", "android"
    device_name = Column(String(100))  # Device name/model
    app_version = Column(String(20))  # App version when registered
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))  # Last successful notification
    
    # Notification preferences stored per device
    notification_preferences = Column(JSON)  # EV thresholds, sports, quiet hours
    
    # Push notification statistics
    total_notifications_sent = Column(Integer, default=0)
    last_notification_sent_at = Column(DateTime(timezone=True))
    notification_failures = Column(Integer, default=0)  # Failed delivery count
    
    # Relationships
    user = relationship("UserProfile")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_device_tokens_user_id', 'user_id'),
        Index('idx_device_tokens_device_token', 'device_token'),
        Index('idx_device_tokens_active', 'is_active'),
        Index('idx_device_tokens_user_active', 'user_id', 'is_active'),
        Index('idx_device_tokens_created_at', 'created_at'),
    )
    
    @staticmethod
    def generate_device_id() -> str:
        """Generate unique device token ID using UUID"""
        import uuid
        return str(uuid.uuid4()) 
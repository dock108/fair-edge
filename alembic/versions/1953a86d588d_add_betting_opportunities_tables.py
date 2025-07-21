"""Add betting opportunities tables

Revision ID: 1953a86d588d
Revises:
Create Date: 2025-06-02 19:07:15.555749

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1953a86d588d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add betting opportunities schema tables."""

    # Create sports lookup table
    op.create_table(
        "sports",
        sa.Column("sport_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("sport_id"),
    )

    # Create leagues lookup table
    op.create_table(
        "leagues",
        sa.Column("league_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sport_id", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["sport_id"],
            ["sports.sport_id"],
        ),
        sa.PrimaryKeyConstraint("league_id"),
    )

    # Create books lookup table
    op.create_table(
        "books",
        sa.Column("book_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("book_type", sa.String(length=20), nullable=True),
        sa.Column("region", sa.String(length=10), nullable=True),
        sa.Column("affiliate_url", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint("book_id"),
    )

    # Create bets table (static metadata)
    op.create_table(
        "bets",
        sa.Column("bet_id", sa.String(length=64), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("league", sa.String(length=50), nullable=True),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column("home_team", sa.String(length=100), nullable=True),
        sa.Column("away_team", sa.String(length=100), nullable=True),
        sa.Column("player_name", sa.String(length=100), nullable=True),
        sa.Column("bet_type", sa.String(length=100), nullable=False),
        sa.Column("market_description", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("outcome_side", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["sport"],
            ["sports.sport_id"],
        ),
        sa.ForeignKeyConstraint(
            ["league"],
            ["leagues.league_id"],
        ),
        sa.PrimaryKeyConstraint("bet_id"),
    )

    # Create indexes for bets table
    op.create_index("idx_bets_sport_league", "bets", ["sport", "league"], unique=False)
    op.create_index("idx_bets_bet_type", "bets", ["bet_type"], unique=False)
    op.create_index("idx_bets_teams", "bets", ["home_team", "away_team"], unique=False)
    op.create_index("idx_bets_created_at", "bets", ["created_at"], unique=False)
    op.create_index(
        "idx_bets_sport_type_created", "bets", ["sport", "bet_type", "created_at"], unique=False
    )

    # Create bet_offers table (time-series data)
    op.create_table(
        "bet_offers",
        sa.Column("offer_id", sa.String(length=36), nullable=False),
        sa.Column("bet_id", sa.String(length=64), nullable=False),
        sa.Column("book", sa.String(length=50), nullable=False),
        sa.Column("odds", sa.JSON(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("fair_odds", sa.JSON(), nullable=True),
        sa.Column("implied_probability", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("volume_indicator", sa.String(length=20), nullable=True),
        sa.Column("available_limits", sa.JSON(), nullable=True),
        sa.Column("offer_metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("refresh_cycle_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["bet_id"],
            ["bets.bet_id"],
        ),
        sa.ForeignKeyConstraint(
            ["book"],
            ["books.book_id"],
        ),
        sa.PrimaryKeyConstraint("offer_id"),
    )

    # Create indexes for bet_offers table
    op.create_index("idx_bet_offers_bet_id", "bet_offers", ["bet_id"], unique=False)
    op.create_index("idx_bet_offers_timestamp", "bet_offers", ["timestamp"], unique=False)
    op.create_index("idx_bet_offers_book", "bet_offers", ["book"], unique=False)
    op.create_index("idx_bet_offers_ev", "bet_offers", ["expected_value"], unique=False)
    op.create_index(
        "idx_bet_offers_bet_timestamp", "bet_offers", ["bet_id", "timestamp"], unique=False
    )
    op.create_index(
        "idx_bet_offers_refresh_cycle", "bet_offers", ["refresh_cycle_id"], unique=False
    )
    op.create_index(
        "idx_offers_recent_high_ev", "bet_offers", ["timestamp", "expected_value"], unique=False
    )


def downgrade() -> None:
    """Remove betting opportunities schema tables."""

    # Drop indexes first
    op.drop_index("idx_offers_recent_high_ev", table_name="bet_offers")
    op.drop_index("idx_bet_offers_refresh_cycle", table_name="bet_offers")
    op.drop_index("idx_bet_offers_bet_timestamp", table_name="bet_offers")
    op.drop_index("idx_bet_offers_ev", table_name="bet_offers")
    op.drop_index("idx_bet_offers_book", table_name="bet_offers")
    op.drop_index("idx_bet_offers_timestamp", table_name="bet_offers")
    op.drop_index("idx_bet_offers_bet_id", table_name="bet_offers")

    op.drop_index("idx_bets_sport_type_created", table_name="bets")
    op.drop_index("idx_bets_created_at", table_name="bets")
    op.drop_index("idx_bets_teams", table_name="bets")
    op.drop_index("idx_bets_bet_type", table_name="bets")
    op.drop_index("idx_bets_sport_league", table_name="bets")

    # Drop tables in correct order (child tables first)
    op.drop_table("bet_offers")
    op.drop_table("bets")
    op.drop_table("books")
    op.drop_table("leagues")
    op.drop_table("sports")

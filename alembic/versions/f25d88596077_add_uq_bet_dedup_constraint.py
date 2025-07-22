"""add uq_bet_dedup constraint

Revision ID: f25d88596077
Revises: 1953a86d588d
Create Date: 2025-06-03 20:15:34.485861

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f25d88596077"
down_revision: Union[str, None] = "1953a86d588d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add event_time, sha_key fields and composite unique constraint to bets table."""
    # Add new columns to bets table
    op.add_column(
        "bets",
        sa.Column(
            "event_time",
            sa.DateTime(),
            nullable=True))
    op.add_column(
        "bets",
        sa.Column(
            "sha_key",
            sa.String(
                length=64),
            nullable=True))

    # Add composite unique constraint for deduplication
    op.create_unique_constraint(
        "uq_bet_dedup", "bets", [
            "sport", "league", "bet_type", "event_time", "sha_key"])


def downgrade() -> None:
    """Remove the unique constraint and new columns."""
    # Drop the unique constraint
    op.drop_constraint("uq_bet_dedup", "bets", type_="unique")

    # Drop the new columns
    op.drop_column("bets", "sha_key")
    op.drop_column("bets", "event_time")

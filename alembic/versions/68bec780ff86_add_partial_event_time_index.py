"""add_partial_event_time_index

Revision ID: 68bec780ff86
Revises: 43d5ddf9785d
Create Date: 2025-06-03 20:40:21.674444

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68bec780ff86"
down_revision: Union[str, None] = "43d5ddf9785d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optimized index for event time lookups."""
    # Create index for event_time to optimize upcoming events queries
    # Note: PostgreSQL doesn't allow time-based partial indexes with immutable functions
    # So we create a regular index that will still provide good performance
    op.create_index(
        "idx_bet_event_time_optimized",
        "bets",
        ["event_time"],
        postgresql_using="btree")


def downgrade() -> None:
    """Remove optimized index."""
    op.drop_index("idx_bet_event_time_optimized", table_name="bets")

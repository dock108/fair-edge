"""add_enum_types_only

Revision ID: 43d5ddf9785d
Revises: f25d88596077
Create Date: 2025-06-03 20:35:21.674444

"""

from typing import Sequence, Union

from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43d5ddf9785d"
down_revision: Union[str, None] = "f25d88596077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create enum types for future use."""
    # Create enum types for better data integrity
    volume_indicator_enum = postgresql.ENUM(
        "HIGH", "MEDIUM", "LOW", "UNKNOWN", name="volume_indicator_enum"
    )
    volume_indicator_enum.create(op.get_bind())

    book_type_enum = postgresql.ENUM(
        "US_BOOK", "EXCHANGE", "SHARP", "OFFSHORE", name="book_type_enum"
    )
    book_type_enum.create(op.get_bind())

    region_enum = postgresql.ENUM(
        "US", "EU", "UK", "AU", "GLOBAL", name="region_enum")
    region_enum.create(op.get_bind())

    user_role_enum = postgresql.ENUM(
        "FREE", "SUBSCRIBER", "ADMIN", name="user_role_enum")
    user_role_enum.create(op.get_bind())

    subscription_status_enum = postgresql.ENUM(
        "NONE",
        "ACTIVE",
        "CANCELLED",
        "EXPIRED",
        "TRIAL",
        name="subscription_status_enum",
    )
    subscription_status_enum.create(op.get_bind())


def downgrade() -> None:
    """Drop enum types."""
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS volume_indicator_enum")
    op.execute("DROP TYPE IF EXISTS book_type_enum")
    op.execute("DROP TYPE IF EXISTS region_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
    op.execute("DROP TYPE IF EXISTS subscription_status_enum")

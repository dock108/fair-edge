"""Update UserRole enum to support basic and premium tiers

Revision ID: 20241228_001
Revises: f25d88596077
Create Date: 2024-12-28 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20241228_001"
down_revision = "f25d88596077"
branch_labels = None
depends_on = None


def upgrade():
    """Add basic and premium values to user_role_enum"""
    # Add new enum values safely
    # (PostgreSQL allows this without recreating the enum)
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'basic'")
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'premium'")


def downgrade():
    """
    Note: PostgreSQL doesn't support removing enum values directly.
    This migration is effectively irreversible in standard PostgreSQL.

    To rollback, you would need to:
    1. Update all users with 'basic' or 'premium' roles to 'free'
    2. Recreate the enum type without these values
    3. This is not implemented here for safety reasons
    """
    pass

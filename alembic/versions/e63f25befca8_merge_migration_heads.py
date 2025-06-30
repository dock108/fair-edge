"""merge_migration_heads

Revision ID: e63f25befca8
Revises: 20241228_001, 68bec780ff86
Create Date: 2025-06-30 11:01:54.217895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e63f25befca8'
down_revision: Union[str, None] = ('20241228_001', '68bec780ff86')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

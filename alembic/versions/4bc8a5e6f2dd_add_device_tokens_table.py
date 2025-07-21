"""add device tokens table

Revision ID: 4bc8a5e6f2dd
Revises: ea8ef4632eaa
Create Date: 2025-01-18 10:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4bc8a5e6f2dd"
down_revision = "ea8ef4632eaa"
branch_labels = None
depends_on = None


def upgrade():
    # Create device_tokens table
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("device_token", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=10), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=True),
        sa.Column("app_version", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_preferences", sa.JSON(), nullable=True),
        sa.Column("total_notifications_sent", sa.Integer(), nullable=True),
        sa.Column("last_notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_failures", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_token"),
    )

    # Create indexes
    op.create_index("idx_device_tokens_user_id", "device_tokens", ["user_id"], unique=False)
    op.create_index(
        "idx_device_tokens_device_token", "device_tokens", ["device_token"], unique=False
    )
    op.create_index("idx_device_tokens_active", "device_tokens", ["is_active"], unique=False)
    op.create_index(
        "idx_device_tokens_user_active", "device_tokens", ["user_id", "is_active"], unique=False
    )
    op.create_index("idx_device_tokens_created_at", "device_tokens", ["created_at"], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index("idx_device_tokens_created_at", table_name="device_tokens")
    op.drop_index("idx_device_tokens_user_active", table_name="device_tokens")
    op.drop_index("idx_device_tokens_active", table_name="device_tokens")
    op.drop_index("idx_device_tokens_device_token", table_name="device_tokens")
    op.drop_index("idx_device_tokens_user_id", table_name="device_tokens")

    # Drop table
    op.drop_table("device_tokens")

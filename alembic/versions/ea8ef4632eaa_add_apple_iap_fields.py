"""Add Apple In-App Purchase fields to profiles table

Revision ID: ea8ef4632eaa
Revises: e63f25befca8
Create Date: 2025-07-18 16:46:23.311030

This migration adds fields to support Apple In-App Purchase integration:
- apple_transaction_id: Current App Store transaction ID
- apple_original_transaction_id: Original transaction ID for subscription group
- apple_receipt_data: Latest receipt data from App Store
- apple_subscription_group_id: Apple subscription group identifier
- apple_purchase_date: Date of purchase/subscription start
- apple_expires_date: Subscription expiration date
- stripe_customer_id: Stripe customer ID (for web users)
- stripe_subscription_id: Stripe subscription ID (for web users)
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea8ef4632eaa"
down_revision: Union[str, None] = "e63f25befca8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Apple IAP and Stripe fields to profiles table."""
    # Add Apple In-App Purchase fields
    op.add_column("profiles", sa.Column("apple_transaction_id", sa.String(255), nullable=True))
    op.add_column(
        "profiles", sa.Column("apple_original_transaction_id", sa.String(255), nullable=True)
    )
    op.add_column("profiles", sa.Column("apple_receipt_data", sa.Text, nullable=True))
    op.add_column(
        "profiles", sa.Column("apple_subscription_group_id", sa.String(255), nullable=True)
    )
    op.add_column(
        "profiles", sa.Column("apple_purchase_date", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "profiles", sa.Column("apple_expires_date", sa.DateTime(timezone=True), nullable=True)
    )

    # Add Stripe fields for web users (to maintain compatibility)
    op.add_column("profiles", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("profiles", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))

    # Create indexes for efficient lookups
    op.create_index("idx_profiles_apple_transaction_id", "profiles", ["apple_transaction_id"])
    op.create_index(
        "idx_profiles_apple_original_transaction_id", "profiles", ["apple_original_transaction_id"]
    )
    op.create_index("idx_profiles_stripe_customer_id", "profiles", ["stripe_customer_id"])
    op.create_index("idx_profiles_stripe_subscription_id", "profiles", ["stripe_subscription_id"])


def downgrade() -> None:
    """Remove Apple IAP and Stripe fields from profiles table."""
    # Drop indexes first
    op.drop_index("idx_profiles_stripe_subscription_id", table_name="profiles")
    op.drop_index("idx_profiles_stripe_customer_id", table_name="profiles")
    op.drop_index("idx_profiles_apple_original_transaction_id", table_name="profiles")
    op.drop_index("idx_profiles_apple_transaction_id", table_name="profiles")

    # Drop columns
    op.drop_column("profiles", "stripe_subscription_id")
    op.drop_column("profiles", "stripe_customer_id")
    op.drop_column("profiles", "apple_expires_date")
    op.drop_column("profiles", "apple_purchase_date")
    op.drop_column("profiles", "apple_subscription_group_id")
    op.drop_column("profiles", "apple_receipt_data")
    op.drop_column("profiles", "apple_original_transaction_id")
    op.drop_column("profiles", "apple_transaction_id")

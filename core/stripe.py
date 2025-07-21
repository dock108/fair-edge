"""
Stripe integration utilities for bet-intel
Handles subscription management and payment processing
"""
import logging
from typing import Optional

import stripe

from core.auth import UserCtx
from core.settings import settings

# Configure Stripe with secret key if available
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key
else:
    stripe.api_key = None  # Will cause errors if used without proper config

logger = logging.getLogger(__name__)


def _check_stripe_config():
    """Check if Stripe is properly configured"""
    if not settings.stripe_configured:
        raise ValueError(
            "Stripe is not properly configured. Please set STRIPE_SECRET_KEY, "
            "STRIPE_WEBHOOK_SECRET, and STRIPE_PREMIUM_PRICE in your environment variables."
        )


def create_checkout_session(user: UserCtx, price_id: str) -> str:
    """
    Create a Stripe Checkout session for subscription upgrade.

    Args:
        user: UserCtx object containing user information
        price_id: Stripe price ID for the subscription

    Returns:
        str: Checkout session URL for redirecting user to Stripe

    Raises:
        stripe.error.StripeError: If session creation fails
        ValueError: If Stripe is not configured
    """
    _check_stripe_config()

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=user.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.checkout_success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=settings.checkout_cancel_url,
            metadata={"user_id": user.id, "user_email": user.email},
        )

        logger.info(f"Created Stripe checkout session {session.id} for user {user.id}")
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Failed to create Stripe checkout session for user {user.id}: {e}")
        raise


def retrieve_checkout_session(session_id: str) -> Optional[stripe.checkout.Session]:
    """
    Retrieve a Stripe checkout session by ID.

    Args:
        session_id: Stripe checkout session ID

    Returns:
        stripe.checkout.Session or None if not found
    """
    _check_stripe_config()

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve checkout session {session_id}: {e}")
        return None


def construct_webhook_event(payload: bytes, signature: str) -> Optional[stripe.Event]:
    """
    Verify and construct a Stripe webhook event.

    Args:
        payload: Raw request body
        signature: Stripe-Signature header value

    Returns:
        stripe.Event or None if verification fails
    """
    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook secret not configured")
        return None

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
        return event
    except (stripe.error.SignatureVerificationError, ValueError) as e:
        logger.error(f"Failed to verify webhook signature: {e}")
        return None


def get_customer_subscriptions(customer_id: str) -> list:
    """
    Get all subscriptions for a Stripe customer.

    Args:
        customer_id: Stripe customer ID

    Returns:
        list: List of active subscriptions
    """
    _check_stripe_config()

    try:
        subscriptions = stripe.Subscription.list(customer=customer_id, status="active")
        return subscriptions.data
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve subscriptions for customer {customer_id}: {e}")
        return []


def cancel_subscription(subscription_id: str) -> bool:
    """
    Cancel a Stripe subscription.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        bool: True if successfully cancelled
    """
    _check_stripe_config()

    try:
        stripe.Subscription.delete(subscription_id)
        logger.info(f"Successfully cancelled subscription {subscription_id}")
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
        return False

"""
Billing routes for Stripe subscription management
Handles checkout sessions, webhooks, and subscription updates
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
import logging
import stripe

from core.auth import get_current_user, UserCtx
from core.stripe import create_checkout_session, construct_webhook_event
from core.settings import settings
from core.rate_limit import limiter
from db import get_db

router = APIRouter(prefix="/api/billing", tags=["billing"])
logger = logging.getLogger(__name__)

def require_subscriber(user: UserCtx = Depends(get_current_user)) -> UserCtx:
    """Require user to be an active subscriber"""
    if user.role != "subscriber" or user.subscription_status != "active":
        raise HTTPException(
            status_code=403, 
            detail="This feature requires an active subscription"
        )
    return user

class CheckoutRequest(BaseModel):
    plan: str = "premium"  # Default to premium for backward compatibility

@router.post("/create-checkout-session")
async def create_stripe_checkout(
    request: CheckoutRequest,
    user: UserCtx = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription upgrade.
    
    Returns:
        dict: Contains checkout_url for redirecting to Stripe
    """
    try:
        # Check if Stripe is configured
        if not settings.stripe_configured:
            raise HTTPException(
                status_code=503,
                detail="Payment processing is not configured. Please contact support."
            )
        
        # Check if user is already a subscriber
        if user.role == "subscriber" and user.subscription_status == "active":
            raise HTTPException(
                status_code=400, 
                detail="User is already an active subscriber"
            )
        
        # Determine price ID based on plan
        if request.plan == "basic":
            if not settings.stripe_basic_price:
                raise HTTPException(
                    status_code=503,
                    detail="Basic plan is not configured. Please contact support."
                )
            price_id = settings.stripe_basic_price
        elif request.plan == "premium":
            if not settings.stripe_premium_price:
                raise HTTPException(
                    status_code=503,
                    detail="Premium plan is not configured. Please contact support."
                )
            price_id = settings.stripe_premium_price
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid plan. Must be 'basic' or 'premium'."
            )
        
        # Create checkout session
        checkout_url = create_checkout_session(user, price_id)
        
        logger.info(f"Created checkout session for user {user.id}")
        return {"checkout_url": checkout_url}
        
    except ValueError as e:
        # Stripe configuration error
        logger.error(f"Stripe configuration error: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Payment processing is temporarily unavailable"
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stripe/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events for subscription lifecycle management.
    
    Processes:
    - checkout.session.completed: Upgrade user to subscriber
    - customer.subscription.deleted: Downgrade user to free
    - invoice.payment_failed: Handle failed payments
    """
    try:
        # Check if webhooks are configured
        if not settings.stripe_webhook_secret:
            logger.error("Webhook received but Stripe webhook secret not configured")
            raise HTTPException(status_code=503, detail="Webhook processing not configured")
        
        # Get request body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Verify webhook signature and construct event
        event = construct_webhook_event(payload, signature)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        # Handle different event types
        if event["type"] == "checkout.session.completed":
            await _handle_checkout_complete(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.deleted":
            await _handle_subscription_cancelled(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_failed":
            await _handle_payment_failed(event["data"]["object"], db)
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def _handle_checkout_complete(session: dict, db: AsyncSession):
    """
    Handle successful checkout completion.
    Updates user role based on the subscription plan and stores Stripe IDs.
    """
    try:
        customer_email = session.get("customer_email")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        
        if not all([customer_email, subscription_id, customer_id]):
            logger.error("Missing required data in checkout session")
            return
        
        # Get subscription details to determine plan
        subscription = stripe.Subscription.retrieve(subscription_id)
        price_id = subscription.items.data[0].price.id
        
        # Determine user role based on price ID
        if price_id == settings.stripe_basic_price:
            user_role = "basic"
        elif price_id == settings.stripe_premium_price:
            user_role = "premium"
        else:
            # Default to premium for unknown prices (backward compatibility)
            user_role = "premium"
            logger.warning(f"Unknown price ID {price_id}, defaulting to premium role")
        
        # Find user by email
        user_id = await _lookup_user_by_email(customer_email, db)
        if not user_id:
            logger.error(f"User not found for email: {customer_email}")
            return
        
        # Update user profile with subscription info
        await db.execute(
            text("""
                UPDATE profiles 
                SET role = :role,
                    subscription_status = 'active',
                    stripe_customer_id = :customer_id,
                    stripe_subscription_id = :subscription_id,
                    updated_at = NOW()
                WHERE id = :user_id
            """),
            {
                "role": user_role,
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "user_id": user_id
            }
        )
        await db.commit()
        
        logger.info(f"Successfully upgraded user {user_id} to {user_role}")
        
    except Exception as e:
        logger.error(f"Error handling checkout completion: {e}")
        await db.rollback()


async def _handle_subscription_cancelled(subscription: dict, db: AsyncSession):
    """
    Handle subscription cancellation.
    Downgrades user back to free tier.
    """
    try:
        subscription_id = subscription.get("id")
        if not subscription_id:
            logger.error("Missing subscription ID in cancellation event")
            return
        
        # Find user by subscription ID and downgrade
        result = await db.execute(
            text("""
                UPDATE profiles 
                SET role = 'free',
                    subscription_status = 'cancelled',
                    updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
                RETURNING id, email
            """),
            {"subscription_id": subscription_id}
        )
        
        user = result.fetchone()
        if user:
            await db.commit()
            logger.info(f"Successfully downgraded user {user.id} ({user.email}) to free tier")
        else:
            logger.warning(f"No user found for cancelled subscription {subscription_id}")
        
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")
        await db.rollback()


async def _handle_payment_failed(invoice: dict, db: AsyncSession):
    """
    Handle failed payment events.
    Could implement grace period or immediate downgrade based on business rules.
    """
    try:
        customer_id = invoice.get("customer")
        if not customer_id:
            logger.error("Missing customer ID in payment failed event")
            return
        
        # Log the failure for now - implement business logic as needed
        logger.warning(f"Payment failed for customer {customer_id}")
        
        # Optional: Implement grace period or immediate downgrade
        # For now, just log the event
        
    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")


async def _lookup_user_by_email(email: str, db: AsyncSession) -> str:
    """
    Look up user ID by email address.
    
    Args:
        email: User's email address
        db: Database session
        
    Returns:
        str: User ID if found, None otherwise
    """
    try:
        result = await db.execute(
            text("SELECT id FROM profiles WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()
        return user.id if user else None
        
    except Exception as e:
        logger.error(f"Error looking up user by email {email}: {e}")
        return None


@router.get("/subscription-status")
async def get_subscription_status(user: UserCtx = Depends(get_current_user)):
    """
    Get current user's subscription status.
    
    Returns:
        dict: Current subscription information
    """
    return {
        "user_id": user.id,
        "role": user.role,
        "subscription_status": user.subscription_status,
        "is_subscriber": user.role == "subscriber" and user.subscription_status == "active",
        "stripe_configured": settings.stripe_configured
    }


@router.post("/create-portal-session")
@limiter.limit("5/minute")  # Rate limit to prevent abuse
async def create_customer_portal_session(
    request: Request,
    user: UserCtx = Depends(require_subscriber),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Customer Portal session for subscription management.
    
    SUBSCRIBERS ONLY - Allows users to:
    - Update payment methods
    - Cancel subscriptions 
    - View invoices and billing history
    - Change subscription plans
    
    Returns:
        dict: Contains url for redirecting to Stripe Customer Portal
    """
    try:
        # Check if Stripe is configured
        if not settings.stripe_configured:
            raise HTTPException(
                status_code=503,
                detail="Payment processing is not configured. Please contact support."
            )
        
        # Get user's Stripe customer ID from database
        result = await db.execute(
            text("SELECT stripe_customer_id FROM profiles WHERE id = :user_id"),
            {"user_id": user.id}
        )
        user_data = result.fetchone()
        
        if not user_data or not user_data.stripe_customer_id:
            raise HTTPException(
                status_code=404,
                detail="No Stripe customer on file; contact support"
            )
        
        # Create Customer Portal session - Stripe API call
        session = stripe.billing_portal.Session.create(
            customer=user_data.stripe_customer_id,                    # required param
            return_url=f"{settings.checkout_success_url.replace('/upgrade/success', '')}/account",  # where to send them back
        )
        
        logger.info(f"Created customer portal session for subscriber {user.id}")
        return {"url": session.url}  # Match the exact specification format
        
    except HTTPException:
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to create billing portal session"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 
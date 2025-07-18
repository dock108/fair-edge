"""
Apple In-App Purchase API Routes
Handles iOS app subscription management and receipt validation

This module provides endpoints for Apple In-App Purchase integration:
- Receipt validation and subscription activation
- Purchase restoration for users switching devices
- Subscription status checking for premium feature access
- App Store Server-to-Server notification handling

SECURITY:
- All receipts are validated server-side with Apple's APIs
- Rate limiting prevents abuse of validation endpoints
- JWT authentication ensures only logged-in users can validate receipts
- Database updates are atomic and transaction-safe

ENDPOINTS:
- POST /api/iap/validate-receipt: Validate App Store receipt after purchase
- POST /api/iap/restore-purchases: Restore previous purchases from receipt
- GET /api/iap/subscription-status: Get current subscription status
- POST /api/iap/app-store-notifications: Handle Apple server notifications

INTEGRATION:
iOS app flow:
1. User purchases subscription via StoreKit
2. App receives transaction and receipt data
3. App calls /validate-receipt with receipt data
4. Server validates with Apple and updates user role
5. App refreshes user state and unlocks premium features
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging

from core.auth import get_current_user, UserCtx
from core.rate_limit import limiter
from core.settings import settings
from services.apple_iap_service import AppleIAPService

router = APIRouter(prefix="/api/iap", tags=["apple-iap"])
logger = logging.getLogger(__name__)


class ReceiptValidationRequest(BaseModel):
    """Request model for receipt validation"""
    receipt_data: str = Field(..., description="Base64 encoded App Store receipt data")
    
    class Config:
        schema_extra = {
            "example": {
                "receipt_data": "ewoJInNpZ25hdHVyZSIgPSAi..."
            }
        }


class RestorePurchasesRequest(BaseModel):
    """Request model for restore purchases"""
    receipt_data: str = Field(..., description="Base64 encoded App Store receipt data")


@router.post("/validate-receipt")
@limiter.limit("10/minute")  # Rate limit to prevent abuse
async def validate_receipt(
    request: Request,
    validation_request: ReceiptValidationRequest,
    user: UserCtx = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate App Store receipt and update user subscription status
    
    This endpoint is called by the iOS app after a successful purchase
    to validate the receipt with Apple and update the user's subscription status.
    
    Process:
    1. Validate receipt data with Apple's verifyReceipt API
    2. Extract subscription details and expiration date
    3. Update user role and subscription status in database
    4. Return updated subscription information
    
    Returns:
        dict: Validation result with subscription status
    """
    try:
        # Check if Apple IAP is configured
        if not settings.apple_iap_configured:
            raise HTTPException(
                status_code=503,
                detail="Apple In-App Purchase is not configured. Please contact support."
            )
        
        # Validate the receipt with Apple
        result = await AppleIAPService.validate_receipt(
            validation_request.receipt_data, 
            user.id
        )
        
        if result.get("valid"):
            logger.info(f"Successfully validated receipt for user {user.id}")
            return {
                "success": True,
                "subscription_status": result.get("subscription_status"),
                "user_role": result.get("user_role"),
                "expires_date": result.get("expires_date"),
                "product_id": result.get("product_id"),
                "is_active": result.get("is_active", False)
            }
        else:
            error_msg = result.get("error", "Unknown validation error")
            status_code = result.get("status_code")
            
            logger.warning(f"Receipt validation failed for user {user.id}: {error_msg}")
            
            # Return specific error codes for different scenarios
            if status_code == 21006:  # Receipt valid but subscription expired
                return {
                    "success": False,
                    "error": "subscription_expired",
                    "message": "Subscription has expired"
                }
            elif status_code == 21007:  # Sandbox receipt
                return {
                    "success": False,
                    "error": "sandbox_receipt",
                    "message": "Cannot use sandbox receipts in production"
                }
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Receipt validation failed: {error_msg}"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating receipt for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Receipt validation error"
        )


@router.post("/restore-purchases")
@limiter.limit("5/minute")  # Lower rate limit for restore purchases
async def restore_purchases(
    request: Request,
    restore_request: RestorePurchasesRequest,
    user: UserCtx = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Restore previous purchases from App Store receipt
    
    Called when user taps "Restore Purchases" in the iOS app.
    This allows users to restore their subscription on new devices
    or after reinstalling the app.
    
    Returns:
        dict: Restoration result with any found subscriptions
    """
    try:
        # Check if Apple IAP is configured
        if not settings.apple_iap_configured:
            raise HTTPException(
                status_code=503,
                detail="Apple In-App Purchase is not configured. Please contact support."
            )
        
        logger.info(f"Attempting to restore purchases for user {user.id}")
        
        # Attempt to restore purchases
        result = await AppleIAPService.restore_purchases(
            restore_request.receipt_data,
            user.id
        )
        
        if result.get("valid"):
            logger.info(f"Successfully restored purchases for user {user.id}")
            return {
                "success": True,
                "subscription_status": result.get("subscription_status"),
                "user_role": result.get("user_role"),
                "expires_date": result.get("expires_date"),
                "message": "Purchases successfully restored"
            }
        else:
            # Not an error if no purchases found - this is normal
            logger.info(f"No purchases to restore for user {user.id}")
            return {
                "success": False,
                "error": "no_purchases_found",
                "message": "No previous purchases found to restore"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring purchases for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Purchase restoration error"
        )


@router.get("/subscription-status")
async def get_apple_subscription_status(
    user: UserCtx = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's Apple subscription status
    
    Returns current subscription information for the iOS app.
    Checks for expired subscriptions and updates status if needed.
    
    Returns:
        dict: Current subscription status and details
    """
    try:
        status = await AppleIAPService.get_user_subscription_status(user.id)
        
        return {
            "user_id": user.id,
            "role": status.get("role"),
            "subscription_status": status.get("subscription_status"),
            "expires_date": status.get("expires_date"),
            "has_apple_subscription": status.get("has_apple_subscription", False),
            "has_stripe_subscription": status.get("has_stripe_subscription", False),
            "is_subscriber": status.get("is_subscriber", False),
            "apple_iap_configured": settings.apple_iap_configured
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription status for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to get subscription status"
        )


@router.post("/app-store-notifications", include_in_schema=False)
async def handle_app_store_notifications(request: Request):
    """
    Handle App Store Server-to-Server notifications
    
    Apple sends notifications for subscription lifecycle events:
    - DID_RENEW: Subscription was renewed
    - CANCEL: Subscription was cancelled  
    - DID_FAIL_TO_RENEW: Subscription renewal failed
    - INITIAL_BUY: Initial subscription purchase
    - DID_CHANGE_RENEWAL_STATUS: Auto-renewal setting changed
    
    This endpoint is called directly by Apple's servers, not the iOS app.
    """
    try:
        payload = await request.json()
        
        # Log the notification for monitoring
        notification_type = payload.get("notification_type", "unknown")
        logger.info(f"Received App Store notification: {notification_type}")
        
        # Verify notification (basic security - Apple sends over HTTPS)
        # In production, could implement JOSE signature verification
        
        # Process the notification
        success = await AppleIAPService.handle_app_store_notification(payload)
        
        if success:
            return {"status": "received"}
        else:
            logger.error(f"Failed to process App Store notification: {notification_type}")
            raise HTTPException(
                status_code=500, 
                detail="Notification processing failed"
            )
            
    except Exception as e:
        logger.error(f"Error processing App Store notification: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Notification processing error"
        )


@router.post("/refresh-subscription")
@limiter.limit("20/minute")  # Higher limit for background refresh
async def refresh_subscription_status(
    request: Request,
    user: UserCtx = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh user's subscription status
    
    Called by iOS app to sync subscription status without requiring new receipt.
    Useful for checking if subscription has expired or been cancelled.
    
    Returns:
        dict: Current subscription status
    """
    try:
        status = await AppleIAPService.get_user_subscription_status(user.id)
        
        return {
            "success": True,
            "role": status.get("role"),
            "subscription_status": status.get("subscription_status"),
            "expires_date": status.get("expires_date"),
            "is_subscriber": status.get("is_subscriber", False)
        }
        
    except Exception as e:
        logger.error(f"Error refreshing subscription for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to refresh subscription status"
        )


@router.get("/products")
async def get_product_configuration() -> Dict[str, Any]:
    """
    Get Apple IAP product configuration for iOS app
    
    Returns product IDs and pricing information that the iOS app
    needs to configure StoreKit and display subscription options.
    
    Returns:
        dict: Product configuration and pricing
    """
    try:
        if not settings.apple_iap_configured:
            raise HTTPException(
                status_code=503,
                detail="Apple In-App Purchase is not configured"
            )
        
        return {
            "products": {
                "basic_monthly": {
                    "product_id": settings.apple_basic_product_id,
                    "tier": "basic",
                    "billing_period": "monthly",
                    "display_price": "$3.99/month",
                    "features": [
                        "All main betting lines",
                        "Unlimited EV access",
                        "Enhanced filtering and search",
                        "Email support"
                    ]
                },
                "premium_monthly": {
                    "product_id": settings.apple_premium_monthly_product_id,
                    "tier": "premium", 
                    "billing_period": "monthly",
                    "display_price": "$9.99/month",
                    "features": [
                        "All betting markets including props",
                        "Advanced analytics and historical data",
                        "Priority data updates",
                        "Export capabilities",
                        "Priority support"
                    ]
                },
                "premium_yearly": {
                    "product_id": settings.apple_premium_yearly_product_id,
                    "tier": "premium",
                    "billing_period": "yearly",
                    "display_price": "$89.99/year",
                    "savings": "25% off monthly price",
                    "features": [
                        "All betting markets including props",
                        "Advanced analytics and historical data", 
                        "Priority data updates",
                        "Export capabilities",
                        "Priority support"
                    ]
                }
            },
            "bundle_id": settings.apple_bundle_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get product configuration"
        )
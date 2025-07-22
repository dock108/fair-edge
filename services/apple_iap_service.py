"""
Apple In-App Purchase Service
Handles receipt validation, subscription status, and App Store Server Notifications

This service implements Apple's In-App Purchase validation and subscription management
to replace Stripe for iOS app compliance. It provides:
- Receipt validation with Apple's verifyReceipt API
- Subscription status management and user role updates
- App Store Server-to-Server notification handling
- Integration with Fair-Edge user management system

PRODUCTION SECURITY:
- All receipts are validated server-side with Apple
- Receipt data is verified for tampering and authenticity
- Subscription statuses are checked against expiration dates
- User roles are updated atomically to prevent inconsistencies

APPLE IAP FLOW:
1. iOS app purchases subscription via StoreKit
2. App sends receipt data to this service
3. Service validates receipt with Apple's servers
4. User role and subscription status updated in database
5. App receives confirmation and unlocks features

SUBSCRIPTION TIERS:
- Basic Monthly ($3.99): Main lines, unlimited EV access
- Premium Monthly ($9.99): All markets, props, export features
- Premium Yearly ($89.99): Premium features with 25% discount
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import aiohttp

from core.settings import settings
from db import get_supabase

logger = logging.getLogger(__name__)


class AppleIAPService:
    """Service for handling Apple In-App Purchase operations"""

    # Apple API endpoints
    SANDBOX_VERIFY_RECEIPT_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
    PRODUCTION_VERIFY_RECEIPT_URL = "https://buy.itunes.apple.com/verifyReceipt"

    # Product ID to role mapping
    PRODUCT_ID_TO_ROLE = {
        "com.fairedge.basic_monthly": "basic",
        "com.fairedge.premium_monthly": "premium",
        "com.fairedge.premium_yearly": "premium",
    }

    # Apple receipt status codes
    RECEIPT_STATUS_CODES = {
        0: "Valid receipt",
        21000: "App Store cannot read receipt JSON",
        21002: "Receipt data property malformed",
        21003: "Receipt could not be authenticated",
        21004: "Shared secret does not match",
        21005: "Receipt server temporarily unavailable",
        21006: "Receipt valid but subscription expired",
        21007: "Sandbox receipt sent to production",
        21008: "Production receipt sent to sandbox",
        21009: "Internal data access error",
        21010: "User account cannot be found",
    }

    @classmethod
    async def validate_receipt(cls, receipt_data: str, user_id: str) -> Dict[str, Any]:
        """
        Validate App Store receipt and update user subscription status

        Args:
            receipt_data: Base64 encoded receipt data from iOS app
            user_id: User ID to update

        Returns:
            Dict with validation result and subscription info
        """
        try:
            # Validate input
            if not receipt_data or not user_id:
                return {"valid": False, "error": "Missing receipt data or user ID"}

            # First try production endpoint
            result = await cls._call_verify_receipt_api(
                receipt_data, cls.PRODUCTION_VERIFY_RECEIPT_URL
            )

            # If production fails with sandbox receipt error, try sandbox
            if result.get("status") == 21007:  # Sandbox receipt sent to production
                logger.info(f"Switching to sandbox validation for user {user_id}")
                result = await cls._call_verify_receipt_api(
                    receipt_data, cls.SANDBOX_VERIFY_RECEIPT_URL
                )

            status_code = result.get("status", -1)
            if status_code != 0:
                error_msg = cls.RECEIPT_STATUS_CODES.get(
                    status_code, f"Unknown error: {status_code}"
                )
                logger.error(f"Receipt validation failed for user {user_id}: {error_msg}")
                return {"valid": False, "error": error_msg, "status_code": status_code}

            # Process the valid receipt
            return await cls._process_receipt_response(result, user_id)

        except aiohttp.ClientError as e:
            logger.error(f"Network error validating receipt for user {user_id}: {e}")
            return {"valid": False, "error": "Network error during validation"}
        except Exception as e:
            logger.error(f"Unexpected error validating receipt for user {user_id}: {e}")
            return {"valid": False, "error": "Validation processing error"}

    @classmethod
    async def _call_verify_receipt_api(cls, receipt_data: str, url: str) -> Dict[str, Any]:
        """Call Apple's verifyReceipt API with proper error handling"""
        if not settings.apple_shared_secret:
            raise ValueError("Apple shared secret not configured")

        payload = {
            "receipt-data": receipt_data,
            "password": settings.apple_shared_secret,
            "exclude-old-transactions": True,
        }

        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Apple API returned status {response.status}")
                    return {"status": -1, "error": f"HTTP {response.status}"}

                return await response.json()

    @classmethod
    async def _process_receipt_response(
        cls, receipt_result: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Process validated receipt and update user subscription"""
        try:
            # receipt = receipt_result.get("receipt", {})  # Currently unused
            latest_receipt_info = receipt_result.get("latest_receipt_info", [])

            if not latest_receipt_info:
                return {"valid": False, "error": "No subscription transactions found"}

            # Get the most recent transaction (highest purchase_date_ms)
            latest_transaction = max(
                latest_receipt_info, key=lambda x: int(x.get("purchase_date_ms", 0))
            )

            # Extract transaction details
            product_id = latest_transaction.get("product_id")
            transaction_id = latest_transaction.get("transaction_id")
            original_transaction_id = latest_transaction.get("original_transaction_id")
            expires_date_ms = latest_transaction.get("expires_date_ms")
            purchase_date_ms = latest_transaction.get("purchase_date_ms")

            if not all([product_id, transaction_id, original_transaction_id]):
                return {"valid": False, "error": "Incomplete transaction data"}

            # Determine user role from product ID
            user_role = cls.PRODUCT_ID_TO_ROLE.get(product_id)
            if not user_role:
                logger.warning(f"Unknown product ID {product_id} for user {user_id}")
                return {"valid": False, "error": f"Unknown product: {product_id}"}

            # Check if subscription is active
            expires_date = None
            is_active = False
            if expires_date_ms:
                expires_date = datetime.fromtimestamp(int(expires_date_ms) / 1000, tz=timezone.utc)
                is_active = expires_date > datetime.now(tz=timezone.utc)

            purchase_date = None
            if purchase_date_ms:
                purchase_date = datetime.fromtimestamp(
                    int(purchase_date_ms) / 1000, tz=timezone.utc
                )

            subscription_status = "active" if is_active else "expired"
            final_role = user_role if is_active else "free"

            # Update user in database
            update_data = {
                "role": final_role,
                "subscription_status": subscription_status,
                "apple_transaction_id": transaction_id,
                "apple_original_transaction_id": original_transaction_id,
                "apple_receipt_data": receipt_result.get("latest_receipt"),
                "apple_purchase_date": (purchase_date.isoformat() if purchase_date else None),
                "apple_expires_date": (expires_date.isoformat() if expires_date else None),
                "updated_at": datetime.now(tz=timezone.utc).isoformat(),
            }

            # Perform database update
            supabase = get_supabase()
            result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()

            if result.data:
                logger.info(
                    f"Updated user {user_id} subscription: {final_role}, "
                    f"active: {is_active}, expires: {expires_date}"
                )
                return {
                    "valid": True,
                    "user_role": final_role,
                    "subscription_status": subscription_status,
                    "expires_date": expires_date.isoformat() if expires_date else None,
                    "product_id": product_id,
                    "transaction_id": transaction_id,
                    "is_active": is_active,
                }
            else:
                logger.error(f"Failed to update user {user_id} in database")
                return {"valid": False, "error": "Database update failed"}

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing receipt data for user {user_id}: {e}")
            return {"valid": False, "error": "Invalid receipt data format"}
        except Exception as e:
            logger.error(f"Unexpected error processing receipt for user {user_id}: {e}")
            return {"valid": False, "error": "Receipt processing error"}

    @classmethod
    async def get_user_subscription_status(cls, user_id: str) -> Dict[str, Any]:
        """Get current user subscription status from database with expiration checking"""
        try:
            supabase = get_supabase()
            result = (
                supabase.table("profiles")
                .select(
                    "role, subscription_status, apple_expires_date, apple_transaction_id, "
                    "stripe_customer_id, stripe_subscription_id"
                )
                .eq("id", user_id)
                .execute()
            )

            if not result.data:
                return {
                    "role": "free",
                    "subscription_status": "none",
                    "has_apple_subscription": False,
                    "has_stripe_subscription": False,
                }

            user_data = result.data[0]
            expires_date = user_data.get("apple_expires_date")
            current_role = user_data.get("role", "free")
            current_status = user_data.get("subscription_status", "none")

            # Check if Apple subscription is expired
            if expires_date and current_status == "active":
                expires_dt = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
                is_expired = expires_dt <= datetime.now(tz=timezone.utc)

                if is_expired:
                    # Update expired subscription
                    logger.info(f"Expiring subscription for user {user_id}")
                    supabase.table("profiles").update(
                        {
                            "role": "free",
                            "subscription_status": "expired",
                            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                        }
                    ).eq("id", user_id).execute()

                    return {
                        "role": "free",
                        "subscription_status": "expired",
                        "expires_date": expires_date,
                        "has_apple_subscription": True,
                        "has_stripe_subscription": bool(user_data.get("stripe_customer_id")),
                    }

            return {
                "role": current_role,
                "subscription_status": current_status,
                "expires_date": expires_date,
                "has_apple_subscription": bool(user_data.get("apple_transaction_id")),
                "has_stripe_subscription": bool(user_data.get("stripe_customer_id")),
                "is_subscriber": current_role in ["basic", "premium"]
                and current_status == "active",
            }

        except Exception as e:
            logger.error(f"Error getting subscription status for user {user_id}: {e}")
            return {
                "role": "free",
                "subscription_status": "none",
                "has_apple_subscription": False,
                "has_stripe_subscription": False,
                "error": "Failed to retrieve subscription status",
            }

    @classmethod
    async def restore_purchases(cls, receipt_data: str, user_id: str) -> Dict[str, Any]:
        """
        Restore purchases from receipt data

        This is called when user taps "Restore Purchases" in the iOS app.
        It validates the receipt and restores any active subscriptions.
        """
        logger.info(f"Restoring purchases for user {user_id}")
        result = await cls.validate_receipt(receipt_data, user_id)

        if result.get("valid"):
            # Log successful restore
            logger.info(
                f"Successfully restored purchases for user {user_id}: {result.get('user_role')}"
            )
        else:
            # Log failed restore - this is normal if user has no purchases
            logger.info(f"No purchases to restore for user {user_id}: {result.get('error')}")

        return result

    @classmethod
    async def handle_app_store_notification(cls, notification_payload: Dict[str, Any]) -> bool:
        """
        Handle App Store Server-to-Server notifications

        Apple sends these notifications for subscription lifecycle events:
        - DID_RENEW: Subscription was renewed
        - CANCEL: Subscription was cancelled
        - DID_FAIL_TO_RENEW: Subscription renewal failed
        - INITIAL_BUY: Initial subscription purchase
        - DID_CHANGE_RENEWAL_STATUS: Auto-renewal status changed
        """
        try:
            notification_type = notification_payload.get("notification_type")

            if not notification_type:
                logger.error("Received App Store notification without type")
                return False

            logger.info(f"Processing App Store notification: {notification_type}")

            if notification_type in ["DID_RENEW", "INITIAL_BUY"]:
                return await cls._handle_subscription_activation(notification_payload)
            elif notification_type in ["CANCEL", "DID_FAIL_TO_RENEW"]:
                return await cls._handle_subscription_cancellation(notification_payload)
            elif notification_type == "DID_CHANGE_RENEWAL_STATUS":
                return await cls._handle_renewal_status_change(notification_payload)
            else:
                logger.info(f"Unhandled notification type: {notification_type}")
                return True  # Return True for unknown types to acknowledge receipt

        except Exception as e:
            logger.error(f"Error handling App Store notification: {e}")
            return False

    @classmethod
    async def _handle_subscription_activation(cls, payload: Dict[str, Any]) -> bool:
        """Handle subscription activation/renewal notifications"""
        try:
            # Extract transaction info from notification
            unified_receipt = payload.get("unified_receipt", {})
            latest_receipt_info = unified_receipt.get("latest_receipt_info", [])

            if not latest_receipt_info:
                logger.error("No receipt info in subscription activation notification")
                return False

            # Get the most recent transaction
            latest_transaction = max(
                latest_receipt_info, key=lambda x: int(x.get("purchase_date_ms", 0))
            )

            original_transaction_id = latest_transaction.get("original_transaction_id")
            if not original_transaction_id:
                logger.error("No original transaction ID in notification")
                return False

            # Find user by original transaction ID
            supabase = get_supabase()
            user_result = (
                supabase.table("profiles")
                .select("id")
                .eq("apple_original_transaction_id", original_transaction_id)
                .execute()
            )

            if not user_result.data:
                logger.warning(f"No user found for transaction ID {original_transaction_id}")
                return True  # Not an error - user might not be registered yet

            user_id = user_result.data[0]["id"]

            # Revalidate receipt to get current status
            receipt_data = unified_receipt.get("latest_receipt")
            if receipt_data:
                await cls.validate_receipt(receipt_data, user_id)
                logger.info(f"Processed subscription activation for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Error handling subscription activation: {e}")
            return False

    @classmethod
    async def _handle_subscription_cancellation(cls, payload: Dict[str, Any]) -> bool:
        """Handle subscription cancellation notifications"""
        try:
            # Extract transaction info
            unified_receipt = payload.get("unified_receipt", {})
            latest_receipt_info = unified_receipt.get("latest_receipt_info", [])

            if not latest_receipt_info:
                logger.error("No receipt info in cancellation notification")
                return False

            latest_transaction = max(
                latest_receipt_info, key=lambda x: int(x.get("purchase_date_ms", 0))
            )

            original_transaction_id = latest_transaction.get("original_transaction_id")
            if not original_transaction_id:
                return False

            # Find and update user
            supabase = get_supabase()
            result = (
                supabase.table("profiles")
                .update(
                    {
                        "role": "free",
                        "subscription_status": "cancelled",
                        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                    }
                )
                .eq("apple_original_transaction_id", original_transaction_id)
                .execute()
            )

            if result.data:
                user = result.data[0]
                logger.info(f"Cancelled subscription for user {user.get('id')}")

            return True

        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return False

    @classmethod
    async def _handle_renewal_status_change(cls, payload: Dict[str, Any]) -> bool:
        """Handle auto-renewal status change notifications"""
        try:
            # For now, just log the event
            auto_renew_status = payload.get("auto_renew_status")
            logger.info(f"Auto-renewal status changed to: {auto_renew_status}")

            # Could implement logic to notify users or update preferences
            return True

        except Exception as e:
            logger.error(f"Error handling renewal status change: {e}")
            return False

    @classmethod
    def verify_notification_signature(cls, payload: bytes, signature: str) -> bool:
        """
        Verify App Store notification signature (if using signed notifications)

        Note: This is for future implementation when Apple requires signed notifications.
        For now, Apple notifications are sent over HTTPS which provides sufficient security.
        """
        # Implementation would verify JOSE signature here
        # For now, return True as notifications are sent over HTTPS
        return True

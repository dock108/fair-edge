"""
Push Notification Service with Apple Push Notification service (APNs) integration
Handles device token management and notification delivery for iOS clients
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from sqlalchemy import and_, or_

from core.settings import settings
from db import get_db
from models import DeviceToken

logger = logging.getLogger(__name__)


class APNsError(Exception):
    """Custom exception for APNs related errors"""

    pass


class PushNotificationService:
    """
    Service for managing push notifications via Apple Push Notification service (APNs)
    """

    def __init__(self):
        self.apns_base_url = settings.apns_base_url
        self.apns_topic = settings.apns_topic or settings.apple_bundle_id  # Use topic or bundle ID
        self.apns_key_id = settings.apns_key_id
        self.apns_team_id = settings.apns_team_id
        self.apns_private_key = settings.apns_private_key

        # APNs HTTP/2 client for persistent connections
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP/2 client for APNs"""
        if self._http_client is None or self._http_client.is_closed:
            # Configure HTTP/2 client with APNs authentication
            headers = {
                "apns-topic": self.apns_topic,
                "apns-push-type": "alert",
                "authorization": f"bearer {await self._generate_jwt_token()}",
            }

            self._http_client = httpx.AsyncClient(
                http2=True, headers=headers, timeout=httpx.Timeout(30.0)
            )

        return self._http_client

    async def _generate_jwt_token(self) -> str:
        """Generate JWT token for APNs authentication using ES256"""
        try:
            from datetime import datetime, timedelta

            import jwt

            # JWT payload
            payload = {
                "iss": self.apns_team_id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=50),  # Apple recommends < 1 hour
            }

            # JWT header
            headers = {"kid": self.apns_key_id, "alg": "ES256"}

            # Generate token with ES256 algorithm
            token = jwt.encode(payload, self.apns_private_key, algorithm="ES256", headers=headers)

            return token

        except Exception as e:
            logger.error(f"Failed to generate JWT token for APNs: {e}")
            raise APNsError(f"JWT token generation failed: {e}")

    async def register_device_token(
        self,
        user_id: str,
        device_token: str,
        device_type: str = "ios",
        device_name: Optional[str] = None,
        app_version: Optional[str] = None,
        notification_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register or update a device token for push notifications

        Args:
            user_id: User identifier
            device_token: APNs device token
            device_type: Device type (ios/android)
            device_name: Device name/model
            app_version: App version
            notification_preferences: User notification preferences

        Returns:
            Dict with registration status and device info
        """
        try:
            session = next(get_db())

            # Check if device token already exists
            existing_token = (
                session.query(DeviceToken).filter(DeviceToken.device_token == device_token).first()
            )

            if existing_token:
                # Update existing token
                existing_token.user_id = user_id
                existing_token.device_name = device_name or existing_token.device_name
                existing_token.app_version = app_version or existing_token.app_version
                existing_token.is_active = True
                existing_token.updated_at = datetime.now(timezone.utc)

                if notification_preferences:
                    existing_token.notification_preferences = notification_preferences

                session.commit()

                logger.info(f"Updated device token for user {user_id}")
                return {
                    "status": "updated",
                    "device_id": existing_token.id,
                    "message": "Device token updated successfully",
                }
            else:
                # Create new device token entry
                new_device = DeviceToken(
                    id=str(uuid4()),
                    user_id=user_id,
                    device_token=device_token,
                    device_type=device_type,
                    device_name=device_name,
                    app_version=app_version,
                    notification_preferences=notification_preferences or {},
                    created_at=datetime.now(timezone.utc),
                )

                session.add(new_device)
                session.commit()

                logger.info(f"Registered new device token for user {user_id}")
                return {
                    "status": "registered",
                    "device_id": new_device.id,
                    "message": "Device token registered successfully",
                }

        except Exception as e:
            logger.error(f"Failed to register device token: {e}")
            if "session" in locals():
                session.rollback()
            raise
        finally:
            if "session" in locals():
                session.close()

    async def send_opportunity_alert(
        self,
        user_id: str,
        opportunity: Dict[str, Any],
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification for high-value betting opportunity

        Args:
            user_id: Target user ID
            opportunity: Opportunity data dict
            custom_message: Custom notification message

        Returns:
            Dict with delivery status and details
        """
        try:
            session = next(get_db())

            # Get active device tokens for user
            device_tokens = (
                session.query(DeviceToken)
                .filter(and_(DeviceToken.user_id == user_id, DeviceToken.is_active.is_(True)))
                .all()
            )

            if not device_tokens:
                return {
                    "status": "no_devices",
                    "message": "No active devices found for user",
                }

            # Prepare notification payload
            ev_pct = opportunity.get("ev_pct", opportunity.get("EV%", 0))
            event = opportunity.get("event", opportunity.get("Event", "Unknown Event"))
            bet_desc = opportunity.get("bet_desc", opportunity.get("Bet Description", ""))

            title = custom_message or "High Value Opportunity!"
            body = f"{event}: {bet_desc} ({ev_pct:.1f}% EV)"

            payload = {
                "aps": {
                    "alert": {"title": title, "body": body},
                    "badge": 1,
                    "sound": "default",
                    "category": "OPPORTUNITY_ALERT",
                },
                "opportunity_data": {
                    "opportunity_id": opportunity.get("id", str(uuid4())),
                    "ev_pct": ev_pct,
                    "event": event,
                    "bet_desc": bet_desc,
                    "best_odds": opportunity.get("best_odds", ""),
                    "best_source": opportunity.get("best_source", ""),
                },
            }

            # Send to all user devices
            results = []
            for device in device_tokens:
                try:
                    # Check if notification should be sent based on preferences
                    if await self._should_send_notification(device, opportunity):
                        result = await self._send_apns_notification(device.device_token, payload)
                        results.append(
                            {
                                "device_id": device.id,
                                "status": result["status"],
                                "details": result.get("details", ""),
                            }
                        )

                        # Update device statistics
                        if result["status"] == "success":
                            device.total_notifications_sent += 1
                            device.last_notification_sent_at = datetime.now(timezone.utc)
                            device.last_used_at = datetime.now(timezone.utc)
                        else:
                            device.notification_failures += 1

                            # Deactivate device if too many failures
                            if device.notification_failures >= 10:
                                device.is_active = False
                                logger.warning(
                                    f"Deactivated device {device.id} due to repeated failures"
                                )
                    else:
                        results.append(
                            {
                                "device_id": device.id,
                                "status": "skipped",
                                "details": "Notification filtered by user preferences",
                            }
                        )

                except Exception as e:
                    logger.error(f"Failed to send notification to device {device.id}: {e}")
                    results.append({"device_id": device.id, "status": "error", "details": str(e)})

            session.commit()

            success_count = sum(1 for r in results if r["status"] == "success")

            return {
                "status": "completed",
                "devices_targeted": len(device_tokens),
                "notifications_sent": success_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send opportunity alert: {e}")
            if "session" in locals():
                session.rollback()
            raise
        finally:
            if "session" in locals():
                session.close()

    async def send_subscription_update(
        self,
        user_id: str,
        status: str,
        title: str = "Subscription Update",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send subscription status update notification

        Args:
            user_id: Target user ID
            status: Subscription status (active, expired, cancelled)
            title: Notification title
            message: Custom notification message

        Returns:
            Dict with delivery status
        """
        try:
            session = next(get_db())

            # Get active device tokens for user
            device_tokens = (
                session.query(DeviceToken)
                .filter(and_(DeviceToken.user_id == user_id, DeviceToken.is_active.is_(True)))
                .all()
            )

            if not device_tokens:
                return {
                    "status": "no_devices",
                    "message": "No active devices found for user",
                }

            # Prepare notification payload
            default_messages = {
                "active": "Your subscription is now active! Enjoy premium features.",
                "expired": "Your subscription has expired. Renew to continue enjoying premium features.",
                "cancelled": "Your subscription has been cancelled. You can resubscribe anytime.",
            }

            body = message or default_messages.get(status, f"Subscription status: {status}")

            payload = {
                "aps": {
                    "alert": {"title": title, "body": body},
                    "badge": 1,
                    "sound": "default",
                    "category": "SUBSCRIPTION_UPDATE",
                },
                "subscription_data": {
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            # Send to all user devices
            results = []
            for device in device_tokens:
                try:
                    result = await self._send_apns_notification(device.device_token, payload)
                    results.append({"device_id": device.id, "status": result["status"]})

                    # Update statistics
                    if result["status"] == "success":
                        device.total_notifications_sent += 1
                        device.last_notification_sent_at = datetime.now(timezone.utc)
                        device.last_used_at = datetime.now(timezone.utc)
                    else:
                        device.notification_failures += 1

                except Exception as e:
                    logger.error(f"Failed to send subscription update to device {device.id}: {e}")
                    results.append({"device_id": device.id, "status": "error", "details": str(e)})

            session.commit()

            success_count = sum(1 for r in results if r["status"] == "success")

            return {
                "status": "completed",
                "devices_targeted": len(device_tokens),
                "notifications_sent": success_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send subscription update: {e}")
            if "session" in locals():
                session.rollback()
            raise
        finally:
            if "session" in locals():
                session.close()

    async def send_system_notification(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        category: str = "SYSTEM_NOTIFICATION",
    ) -> Dict[str, Any]:
        """
        Send system-wide notification to multiple users

        Args:
            user_ids: List of target user IDs
            title: Notification title
            message: Notification message
            category: Notification category

        Returns:
            Dict with delivery results
        """
        try:
            session = next(get_db())

            # Get active device tokens for all users
            device_tokens = (
                session.query(DeviceToken)
                .filter(and_(DeviceToken.user_id.in_(user_ids), DeviceToken.is_active == True))
                .all()
            )

            if not device_tokens:
                return {
                    "status": "no_devices",
                    "message": "No active devices found for target users",
                }

            # Prepare notification payload
            payload = {
                "aps": {
                    "alert": {"title": title, "body": message},
                    "badge": 1,
                    "sound": "default",
                    "category": category,
                },
                "system_data": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "category": category,
                },
            }

            # Send to all devices
            results = []
            for device in device_tokens:
                try:
                    result = await self._send_apns_notification(device.device_token, payload)
                    results.append(
                        {
                            "user_id": device.user_id,
                            "device_id": device.id,
                            "status": result["status"],
                        }
                    )

                    # Update statistics
                    if result["status"] == "success":
                        device.total_notifications_sent += 1
                        device.last_notification_sent_at = datetime.now(timezone.utc)
                        device.last_used_at = datetime.now(timezone.utc)
                    else:
                        device.notification_failures += 1

                except Exception as e:
                    logger.error(f"Failed to send system notification to device {device.id}: {e}")
                    results.append(
                        {
                            "user_id": device.user_id,
                            "device_id": device.id,
                            "status": "error",
                            "details": str(e),
                        }
                    )

            session.commit()

            success_count = sum(1 for r in results if r["status"] == "success")

            return {
                "status": "completed",
                "devices_targeted": len(device_tokens),
                "notifications_sent": success_count,
                "users_reached": len(
                    set(r["user_id"] for r in results if r["status"] == "success")
                ),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
            if "session" in locals():
                session.rollback()
            raise
        finally:
            if "session" in locals():
                session.close()

    async def _send_apns_notification(
        self, device_token: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification via APNs HTTP/2 API

        Args:
            device_token: Target device token
            payload: Notification payload

        Returns:
            Dict with delivery status
        """
        try:
            client = await self._get_http_client()

            # APNs endpoint URL
            url = f"{self.apns_base_url}/3/device/{device_token}"

            # Send notification
            response = await client.post(
                url,
                json=payload,
                headers={
                    "apns-expiration": str(
                        int(datetime.now(timezone.utc).timestamp()) + 3600
                    ),  # 1 hour expiry
                    "apns-priority": "10",  # High priority for alerts
                    "apns-collapse-id": f"opportunity-{payload.get('opportunity_data', {}).get('opportunity_id', 'system')}",
                },
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "apns_id": response.headers.get("apns-id", ""),
                    "details": "Notification sent successfully",
                }
            else:
                error_data = response.json() if response.content else {}
                logger.warning(f"APNs delivery failed: {response.status_code} - {error_data}")

                return {
                    "status": "failed",
                    "error_code": response.status_code,
                    "error_reason": error_data.get("reason", "Unknown error"),
                    "details": error_data,
                }

        except Exception as e:
            logger.error(f"APNs request failed: {e}")
            return {"status": "error", "details": str(e)}

    async def _should_send_notification(
        self, device: DeviceToken, opportunity: Dict[str, Any]
    ) -> bool:
        """
        Check if notification should be sent based on user preferences and quiet hours

        Args:
            device: Device token object with preferences
            opportunity: Opportunity data

        Returns:
            Bool indicating if notification should be sent
        """
        try:
            prefs = device.notification_preferences or {}

            # Check EV threshold
            ev_threshold = prefs.get("ev_threshold", 5.0)  # Default 5%
            opportunity_ev = opportunity.get("ev_pct", opportunity.get("EV%", 0))

            if opportunity_ev < ev_threshold:
                return False

            # Check sport preferences
            enabled_sports = prefs.get("enabled_sports", [])
            if enabled_sports:
                opportunity_sport = opportunity.get("sport", "").upper()
                if opportunity_sport not in [sport.upper() for sport in enabled_sports]:
                    return False

            # Check quiet hours
            quiet_hours_enabled = prefs.get("quiet_hours_enabled", False)
            if quiet_hours_enabled:
                now = datetime.now()
                current_hour = now.hour

                quiet_start = prefs.get("quiet_hours_start", 22)  # 10 PM default
                quiet_end = prefs.get("quiet_hours_end", 8)  # 8 AM default

                # Handle quiet hours that span midnight
                if quiet_start > quiet_end:
                    if current_hour >= quiet_start or current_hour < quiet_end:
                        return False
                else:
                    if quiet_start <= current_hour < quiet_end:
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking notification preferences: {e}")
            return True  # Default to sending if preferences check fails

    async def cleanup_inactive_tokens(self, days_inactive: int = 30) -> Dict[str, Any]:
        """
        Clean up device tokens that haven't been used recently

        Args:
            days_inactive: Number of days of inactivity before cleanup

        Returns:
            Dict with cleanup results
        """
        try:
            session = next(get_db())

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)

            # Find inactive tokens
            inactive_tokens = (
                session.query(DeviceToken)
                .filter(
                    or_(
                        DeviceToken.last_used_at < cutoff_date,
                        and_(
                            DeviceToken.last_used_at.is_(None),
                            DeviceToken.created_at < cutoff_date,
                        ),
                    )
                )
                .all()
            )

            # Deactivate tokens
            deactivated_count = 0
            for token in inactive_tokens:
                token.is_active = False
                deactivated_count += 1

            session.commit()

            logger.info(f"Deactivated {deactivated_count} inactive device tokens")

            return {
                "status": "completed",
                "deactivated_tokens": deactivated_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup inactive tokens: {e}")
            if "session" in locals():
                session.rollback()
            raise
        finally:
            if "session" in locals():
                session.close()

    async def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all registered devices for a user

        Args:
            user_id: User identifier

        Returns:
            List of device information dicts
        """
        try:
            session = next(get_db())

            devices = session.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()

            return [
                {
                    "device_id": device.id,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "app_version": device.app_version,
                    "is_active": device.is_active,
                    "created_at": (device.created_at.isoformat() if device.created_at else None),
                    "last_used_at": (
                        device.last_used_at.isoformat() if device.last_used_at else None
                    ),
                    "total_notifications_sent": device.total_notifications_sent,
                    "notification_failures": device.notification_failures,
                    "notification_preferences": device.notification_preferences or {},
                }
                for device in devices
            ]

        except Exception as e:
            logger.error(f"Failed to get user devices: {e}")
            raise
        finally:
            if "session" in locals():
                session.close()


# Global service instance
push_notification_service = PushNotificationService()

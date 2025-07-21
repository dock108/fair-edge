"""
Session Management for Production Authentication
Handles httpOnly cookies and CSRF protection
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, Request, Response
from jwt import PyJWTError

from core.auth import UserCtx
from core.settings import settings


class SessionManager:
    """Manages secure session cookies and CSRF tokens"""

    # Cookie names
    AUTH_COOKIE = "sb_session"
    CSRF_COOKIE = "csrf_token"

    # CSRF token lifetime (shorter than session)
    CSRF_LIFETIME_MINUTES = 30

    @classmethod
    def set_auth_cookie(cls, response: Response, access_token: str, user_data: dict) -> str:
        """
        Set secure httpOnly authentication cookie
        Returns CSRF token for client-side storage
        """
        # Set the auth cookie (httpOnly, not secure for localhost development)
        response.set_cookie(
            key=cls.AUTH_COOKIE,
            value=access_token,
            max_age=3600,  # 1 hour in seconds
            httponly=True,  # Block JS access
            secure=False,  # Always False for development (localhost doesn't use HTTPS)
            samesite="lax",  # CSRF protection
            path="/",  # Ensure cookie is available for all paths
            domain=None,  # Use default domain
        )

        # Generate CSRF token
        csrf_token = cls._generate_csrf_token(user_data.get("id", ""))

        # Set CSRF cookie (readable by JS for API calls)
        response.set_cookie(
            key=cls.CSRF_COOKIE,
            value=csrf_token,
            max_age=cls.CSRF_LIFETIME_MINUTES * 60,
            httponly=False,  # JS needs to read this
            secure=False,  # Always False for development
            samesite="lax",
            path="/",  # Ensure cookie is available for all paths
            domain=None,
        )

        return csrf_token

    @classmethod
    def clear_auth_cookies(cls, response: Response):
        """Clear authentication and CSRF cookies"""
        response.delete_cookie(key=cls.AUTH_COOKIE, path="/", samesite="lax")
        response.delete_cookie(key=cls.CSRF_COOKIE, path="/", samesite="lax")

    @classmethod
    def get_auth_token_from_cookie(cls, request: Request) -> Optional[str]:
        """Extract auth token from httpOnly cookie"""
        return request.cookies.get(cls.AUTH_COOKIE)

    @classmethod
    def get_csrf_token_from_cookie(cls, request: Request) -> Optional[str]:
        """Extract CSRF token from cookie"""
        return request.cookies.get(cls.CSRF_COOKIE)

    @classmethod
    def validate_csrf_token(cls, request: Request, provided_token: Optional[str] = None) -> bool:
        """
        Validate CSRF token using double-submit pattern
        Compares cookie token with header/form token
        """
        # Get CSRF token from cookie
        cookie_token = cls.get_csrf_token_from_cookie(request)
        if not cookie_token:
            return False

        # Get CSRF token from header or form data
        if provided_token is None:
            # Try header first
            provided_token = request.headers.get("X-CSRF-Token")

            # If not in header, try form data (for multipart forms)
            if not provided_token and hasattr(request, "form"):
                form_data = getattr(request, "_form_data", None)
                if form_data:
                    provided_token = form_data.get("csrf_token")

        if not provided_token:
            return False

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(cookie_token, provided_token)

    @classmethod
    def _generate_csrf_token(cls, user_id: str) -> str:
        """Generate cryptographically secure CSRF token"""
        # Create token with timestamp and user_id for validation
        timestamp = int(datetime.utcnow().timestamp())
        random_bytes = secrets.token_bytes(16)

        # Create HMAC with secret key
        message = f"{user_id}:{timestamp}:{random_bytes.hex()}"
        signature = hmac.new(
            settings.supabase_jwt_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        return f"{timestamp}:{random_bytes.hex()}:{signature}"

    @classmethod
    def _validate_csrf_token_structure(cls, token: str, user_id: str) -> bool:
        """Validate CSRF token structure and expiration"""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False

            timestamp_str, random_hex, signature = parts
            timestamp = int(timestamp_str)

            # Check if token is expired
            token_time = datetime.fromtimestamp(timestamp)
            if datetime.utcnow() - token_time > timedelta(minutes=cls.CSRF_LIFETIME_MINUTES):
                return False

            # Validate signature
            message = f"{user_id}:{timestamp_str}:{random_hex}"
            expected_signature = hmac.new(
                settings.supabase_jwt_secret.encode(), message.encode(), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, TypeError):
            return False


def get_current_user_from_cookie(request: Request) -> Optional[UserCtx]:
    """
    Extract and validate user from session cookie
    Alternative to header-based auth for cookie authentication
    """
    token = SessionManager.get_auth_token_from_cookie(request)
    if not token:
        return None

    try:
        # Validate JWT token (same logic as core.auth but from cookie)
        # Note: PyJWT doesn't verify audience by default, so no options needed
        payload = jwt.decode(
            token, settings.supabase_jwt_secret, algorithms=[settings.supabase_jwt_algorithm]
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            return None

        # Extract role from user metadata (same logic as core.auth)
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})

        role = user_metadata.get("role") or app_metadata.get("role") or "free"

        subscription_status = (
            user_metadata.get("subscription_status")
            or app_metadata.get("subscription_status")
            or "inactive"
        )

        return UserCtx(id=user_id, email=email, role=role, subscription_status=subscription_status)

    except PyJWTError:
        return None


# Dependency for endpoints that require both auth and CSRF validation
def generate_csrf_token() -> str:
    """Generate a simple CSRF token"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, stored_token: Optional[str]) -> bool:
    """Validate CSRF token"""
    return token and stored_token and hmac.compare_digest(token, stored_token)


def require_csrf_validation(request: Request) -> bool:
    """
    Dependency that validates CSRF token for state-changing operations
    Use this for POST/PUT/DELETE endpoints (except logout and webhooks)
    """
    if not SessionManager.validate_csrf_token(request):
        raise HTTPException(status_code=403, detail="CSRF token validation failed")
    return True

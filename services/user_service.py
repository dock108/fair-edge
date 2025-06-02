"""
User Service for handling authentication patterns and user context
Centralizes all user-related logic that was duplicated across endpoints
"""
from typing import Dict, Any
from fastapi import Request
import logging

from core.session import get_current_user_from_cookie
from core.auth import UserCtx

logger = logging.getLogger(__name__)


def get_user_or_guest(request: Request) -> UserCtx:
    """
    Get authenticated user or create guest user context
    This replaces the repeated pattern throughout the codebase
    
    Returns:
        UserCtx: Either authenticated user or guest user with free tier access
    """
    try:
        user = get_current_user_from_cookie(request)
        if user:
            return user
    except Exception as e:
        logger.debug(f"Failed to get user from cookie: {e}")
    
    # Create guest user context for free tier access
    return UserCtx(
        id="guest",
        email="guest@example.com",
        role="free",
        subscription_status="none"
    )


def is_guest_user(user: UserCtx) -> bool:
    """Check if user is a guest (unauthenticated)"""
    return user.id == "guest"


def create_user_response_metadata(user: UserCtx) -> Dict[str, Any]:
    """
    Create standardized user metadata for API responses
    
    Returns:
        Dict containing user role, guest status, and other metadata
    """
    return {
        "role": user.role,
        "is_guest": is_guest_user(user),
        "user_email": user.email if not is_guest_user(user) else None,
        "subscription_status": user.subscription_status
    }


def get_role_features(user_role: str) -> Dict[str, Any]:
    """
    Get feature access configuration for a user role
    Centralizes role-based feature access logic
    """
    from core.constants import ROLE_FEATURES
    return ROLE_FEATURES.get(user_role, ROLE_FEATURES["free"])


class UserContextManager:
    """
    Context manager for handling user authentication patterns
    Provides a clean interface for user-related operations
    """
    
    def __init__(self, request: Request):
        self.request = request
        self._user = None
    
    @property
    def user(self) -> UserCtx:
        """Lazy load user context"""
        if self._user is None:
            self._user = get_user_or_guest(self.request)
        return self._user
    
    @property
    def is_guest(self) -> bool:
        """Check if current user is guest"""
        return is_guest_user(self.user)
    
    @property
    def role(self) -> str:
        """Get user role"""
        return self.user.role
    
    @property
    def features(self) -> Dict[str, Any]:
        """Get user's feature access"""
        return get_role_features(self.user.role)
    
    def get_response_metadata(self) -> Dict[str, Any]:
        """Get user metadata for API responses"""
        return create_user_response_metadata(self.user) 
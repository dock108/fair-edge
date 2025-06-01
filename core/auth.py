"""
Supabase JWT Authentication for FastAPI
Handles JWT validation, role-based authorization, and database lookups
"""
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
import logging

from core.config import settings
from db import get_db

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


class UserCtx(BaseModel):
    """User context model for authenticated requests"""
    id: str
    email: Optional[str] = None
    role: str = "free"            # Default fallback
    subscription_status: str = "none"
    
    class Config:
        arbitrary_types_allowed = True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserCtx:
    """
    Main authentication dependency used by all protected routes
    Validates JWT token and fetches user profile from database
    """
    token = credentials.credentials
    
    try:
        # Decode and validate JWT using Supabase JWT secret
        # Note: We disable audience verification since we're doing our own validation
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False}  # Disable audience verification
        )
    except JWTError as exc:
        logger.warning(f"JWT validation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed JWT (no sub claim)"
        )

    # Extract email from JWT payload
    email = payload.get("email")

    # Fetch role & subscription status from profiles table
    try:
        result = await db.execute(
            text("SELECT id, email, role, subscription_status FROM profiles WHERE id = :user_id"),
            {"user_id": user_id}
        )
        profile = result.fetchone()

        if profile:
            return UserCtx(
                id=str(profile[0]),
                email=profile[1] or email,
                role=profile[2] or "free",
                subscription_status=profile[3] or "none",
            )
        else:
            # Profile not found - auto-create default context
            # In production, you might want to create the profile record here
            logger.info(f"Profile not found for user {user_id}, using defaults")
            return UserCtx(id=user_id, email=email)
            
    except Exception as db_error:
        logger.error(f"Database error fetching user profile: {db_error}")
        # Graceful fallback to JWT-only context
        return UserCtx(id=user_id, email=email)


def require_role(*accepted_roles: str):
    """
    Dependency factory for role-based access control
    
    Usage:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        @app.get("/premium", dependencies=[Depends(require_role("subscriber", "admin"))])
    """
    async def checker(user: UserCtx = Depends(get_current_user)) -> UserCtx:
        if user.role not in accepted_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {accepted_roles}, Current: {user.role}"
            )
        return user
    return checker


def require_subscription():
    """
    Dependency for subscription-required endpoints
    Allows both subscribers and admins
    """
    async def checker(user: UserCtx = Depends(get_current_user)) -> UserCtx:
        if user.role not in ["subscriber", "admin"] and user.subscription_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required"
            )
        return user
    return checker


# Convenience dependencies
require_subscriber = require_role("subscriber", "admin")
require_admin = require_role("admin")


async def get_optional_user(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Optional[UserCtx]:
    """
    Optional authentication dependency
    Returns UserCtx if valid token provided, None otherwise
    Useful for endpoints that behave differently for authenticated vs anonymous users
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return await get_current_user(credentials, db)
    except HTTPException:
        # Invalid token - return None instead of raising exception
        return None 
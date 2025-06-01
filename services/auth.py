"""
Authentication utilities for FastAPI app
Handles Supabase JWT validation and role-based authorization
"""
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import os
import logging

from db import get_db

logger = logging.getLogger(__name__)

# Supabase JWT configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # Use anon key for JWT verification
JWT_ALGORITHM = "HS256"  # Supabase defaults to HS256

# HTTP Bearer token security
security = HTTPBearer()

class User(BaseModel):
    """User model for authenticated requests"""
    id: str
    email: Optional[str] = None
    role: str = "free"  # Default fallback
    subscription_status: str = "none"
    
    class Config:
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed = True


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Basic JWT validation without database lookup
    Returns user with default role
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="JWT secret not configured"
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT: missing user ID"
            )
        
        return User(id=user_id, email=email)
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    JWT validation with database lookup for role and subscription info
    This is the main auth dependency to use for protected routes
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="JWT secret not configured"
        )
    
    token = credentials.credentials
    try:
        # Decode and validate JWT
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT: missing user ID"
            )
        
        # Query user profile from database
        try:
            result = await db.execute(
                text("SELECT id, email, role, subscription_status FROM profiles WHERE id = :user_id"),
                {"user_id": user_id}
            )
            profile = result.fetchone()
            
            if profile:
                return User(
                    id=str(profile[0]),
                    email=profile[1] or email,
                    role=profile[2] or "free",
                    subscription_status=profile[3] or "none"
                )
            else:
                # Profile not found - create a default user
                # In a real app, you might want to create the profile here
                logger.warning(f"Profile not found for user {user_id}, using defaults")
                return User(
                    id=user_id,
                    email=email,
                    role="free",
                    subscription_status="none"
                )
                
        except Exception as db_error:
            logger.error(f"Database error fetching user profile: {db_error}")
            # Fall back to basic user info from JWT
            return User(
                id=user_id,
                email=email,
                role="free",
                subscription_status="none"
            )
            
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def require_role(required_role: str):
    """
    Dependency factory for role-based access control
    Usage: @app.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def check_role(user: User = Depends(get_current_user_with_role)):
        role_hierarchy = {
            "free": 0,
            "subscriber": 1,
            "admin": 2
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}, Current: {user.role}"
            )
        
        return user
    
    return check_role


def require_subscription():
    """
    Dependency for subscription-required endpoints
    """
    async def check_subscription(user: User = Depends(get_current_user_with_role)):
        if user.role not in ["subscriber", "admin"] and user.subscription_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required"
            )
        return user
    
    return check_subscription


# Optional user dependency (doesn't raise exception if not authenticated)
async def get_optional_user(
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns User if valid token provided, None otherwise
    Useful for endpoints that behave differently for authenticated vs anonymous users
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return await get_current_user_with_role(credentials, db)
    except HTTPException:
        return None 
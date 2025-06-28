"""
Authentication and Session Management Routes
Handles user authentication, session management, and logout functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

# Import authentication and session dependencies
from core.auth import get_user_or_none, UserCtx, verify_jwt_token
from core.session import require_csrf_validation, generate_csrf_token, validate_csrf_token
from core.rate_limit import limiter
from core.settings import settings

# Initialize router
router = APIRouter(tags=["authentication"])
logger = logging.getLogger(__name__)

# Pydantic models
class SessionRequest(BaseModel):
    token: str
    remember_me: Optional[bool] = False

class LogoutRequest(BaseModel):
    csrf_token: Optional[str] = None

@router.post("/api/logout")
@limiter.limit("10/minute")
async def logout_user(
    request: Request,
    response: Response,
    user: Optional[UserCtx] = Depends(get_user_or_none)
):
    """
    Basic logout endpoint - clears client-side session
    For enhanced security, use /api/logout-secure with CSRF protection
    """
    try:
        # Clear any session cookies
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=settings.environment == "production",
            httponly=True,
            samesite="lax"
        )
        
        response.delete_cookie(
            key="csrf_token",
            path="/",
            secure=settings.environment == "production",
            samesite="lax"
        )
        
        if user:
            logger.info(f"User logged out: {user.email}")
        else:
            logger.info("Anonymous logout request processed")
        
        return {
            "success": True,
            "message": "Logged out successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return {
            "success": True,  # Always return success for logout
            "message": "Logout completed",
            "note": "Some cleanup may have failed but user is logged out"
        }

@router.post("/api/session")
@limiter.limit("30/minute")
async def create_session(
    session_data: SessionRequest,
    request: Request,
    response: Response
):
    """
    Create a secure session with JWT token and CSRF protection
    Handles both short-term and persistent sessions
    """
    try:
        # Verify the provided JWT token
        user_data = verify_jwt_token(session_data.token)
        
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Generate CSRF token for session protection
        csrf_token = generate_csrf_token()
        
        # Set session duration based on remember_me preference
        if session_data.remember_me:
            max_age = 30 * 24 * 60 * 60  # 30 days
            expires = datetime.now() + timedelta(days=30)
        else:
            max_age = 24 * 60 * 60  # 24 hours
            expires = datetime.now() + timedelta(hours=24)
        
        # Set secure session cookie
        response.set_cookie(
            key="session_token",
            value=session_data.token,
            max_age=max_age,
            expires=expires,
            path="/",
            secure=settings.environment == "production",
            httponly=True,
            samesite="lax"
        )
        
        # Set CSRF token cookie (readable by client for form submissions)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=max_age,
            expires=expires,
            path="/",
            secure=settings.environment == "production",
            httponly=False,  # Client needs to read this for CSRF protection
            samesite="lax"
        )
        
        logger.info(f"Session created for user: {user_data.get('email', 'unknown')}")
        
        return {
            "success": True,
            "message": "Session created successfully",
            "user": {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "role": user_data.get("role", "free")
            },
            "session_info": {
                "expires_at": expires.isoformat(),
                "persistent": session_data.remember_me,
                "csrf_protected": True
            },
            "csrf_token": csrf_token,  # Also return in response for SPA usage
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create session"
        )

@router.post("/api/logout-secure")
@limiter.limit("10/minute")
async def logout_secure(
    request: Request,
    response: Response,
    logout_data: LogoutRequest,
    user: Optional[UserCtx] = Depends(get_user_or_none),
    csrf_token_cookie: Optional[str] = Cookie(None, alias="csrf_token")
):
    """
    Secure logout with CSRF protection
    Recommended for production use to prevent CSRF logout attacks
    """
    try:
        # Validate CSRF token if provided
        csrf_valid = False
        if logout_data.csrf_token and csrf_token_cookie:
            csrf_valid = validate_csrf_token(logout_data.csrf_token, csrf_token_cookie)
        elif not logout_data.csrf_token and not csrf_token_cookie:
            # Allow logout without CSRF if no tokens present (user already logged out)
            csrf_valid = True
        
        if not csrf_valid:
            logger.warning(f"CSRF validation failed for logout attempt from {request.client.host}")
            raise HTTPException(
                status_code=403,
                detail="Invalid CSRF token. Please refresh the page and try again."
            )
        
        # Clear all session cookies securely
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=settings.environment == "production",
            httponly=True,
            samesite="lax"
        )
        
        response.delete_cookie(
            key="csrf_token",
            path="/",
            secure=settings.environment == "production",
            samesite="lax"
        )
        
        # Log the secure logout
        if user:
            logger.info(f"Secure logout completed for user: {user.email}")
        else:
            logger.info("Secure logout processed (no active session)")
        
        return {
            "success": True,
            "message": "Secure logout completed",
            "session_cleared": True,
            "csrf_validated": csrf_valid,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during secure logout: {e}")
        # Always clear cookies on logout errors for security
        response.delete_cookie(key="session_token", path="/")
        response.delete_cookie(key="csrf_token", path="/")
        
        return {
            "success": True,
            "message": "Logout completed with cleanup",
            "note": "Session cleared due to error during logout process"
        }

@router.get("/api/session/user")
@limiter.limit("60/minute")
async def get_session_user(
    request: Request,
    user: Optional[UserCtx] = Depends(get_user_or_none)
):
    """
    Get current session user information
    Returns user data if authenticated, null if not
    """
    try:
        if not user:
            return {
                "authenticated": False,
                "user": None,
                "session_status": "no_active_session",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "subscription_status": getattr(user, 'subscription_status', 'free'),
                "permissions": {
                    "can_access_premium": user.role in ["subscriber", "admin"],
                    "can_export_data": user.role in ["subscriber", "admin"],
                    "can_access_admin": user.role == "admin",
                    "api_rate_limit": "unlimited" if user.role == "admin" else "standard"
                }
            },
            "session_status": "active",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting session user: {e}")
        return {
            "authenticated": False,
            "user": None,
            "session_status": "error",
            "error": "Failed to retrieve session information",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/api/user-info")
@limiter.limit("60/minute")
async def get_user_info(
    request: Request,
    user: Optional[UserCtx] = Depends(get_user_or_none)
):
    """
    Get detailed user information and capabilities
    Legacy endpoint maintained for compatibility
    """
    try:
        if not user:
            return {
                "authenticated": False,
                "role": "anonymous",
                "capabilities": {
                    "max_opportunities": 10,
                    "ev_threshold": -2.0,
                    "market_access": ["main_lines"],
                    "export_access": False
                },
                "message": "Not authenticated"
            }
        
        # Define role-based capabilities
        capabilities = {
            "free": {
                "max_opportunities": 10,
                "ev_threshold": -2.0,
                "market_access": ["main_lines"],
                "export_access": False,
                "refresh_access": False
            },
            "basic": {
                "max_opportunities": None,
                "ev_threshold": None,
                "market_access": ["main_lines"],
                "export_access": False,
                "refresh_access": False
            },
            "subscriber": {
                "max_opportunities": None,
                "ev_threshold": None,
                "market_access": ["main_lines", "props", "totals", "spreads"],
                "export_access": True,
                "refresh_access": False
            },
            "admin": {
                "max_opportunities": None,
                "ev_threshold": None,
                "market_access": ["all"],
                "export_access": True,
                "refresh_access": True,
                "admin_access": True
            }
        }
        
        user_capabilities = capabilities.get(user.role, capabilities["free"])
        
        return {
            "authenticated": True,
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "subscription_status": getattr(user, 'subscription_status', 'free'),
            "capabilities": user_capabilities,
            "session_info": {
                "last_activity": datetime.now().isoformat(),
                "api_version": "v1"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
        )
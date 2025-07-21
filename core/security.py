"""
Security utilities for cookie management and authentication
Handles secure cookie setting based on environment configuration
"""
from fastapi import Response

from core.settings import get_settings


def set_auth_cookie(resp: Response, token: str, max_age_seconds: int = None):
    """
    Set secure httpOnly authentication cookie with environment-appropriate settings

    Args:
        resp: FastAPI Response object
        token: JWT token to store in cookie
        max_age_seconds: Cookie lifetime in seconds (defaults to 1 hour)
    """
    cfg = get_settings()
    secure = cfg.app_env == "prod"

    if max_age_seconds is None:
        max_age_seconds = 3600  # Default 1 hour

    resp.set_cookie(
        "access_token",
        token,
        httponly=True,  # Prevent XSS
        secure=secure,  # HTTPS only in production
        samesite="strict",  # CSRF protection
        max_age=max_age_seconds,
        path="/",
    )


def clear_auth_cookie(resp: Response):
    """
    Clear the authentication cookie

    Args:
        resp: FastAPI Response object
    """
    resp.delete_cookie("access_token", path="/", samesite="strict")


def fail_fast_on_unsafe_defaults():
    """
    Check for unsafe default values in production and fail fast
    This prevents accidentally running with placeholder secrets
    """
    cfg = get_settings()

    if cfg.app_env == "prod":
        unsafe_defaults = []

        if cfg.admin_secret == "CHANGE_ME":
            unsafe_defaults.append("ADMIN_SECRET")
        if "CHANGE_ME" in str(cfg.supabase_url):
            unsafe_defaults.append("SUPABASE_URL")
        if cfg.supabase_jwt_secret == "CHANGE_ME":
            unsafe_defaults.append("SUPABASE_JWT_SECRET")
        if cfg.odds_api_key == "CHANGE_ME":
            unsafe_defaults.append("ODDS_API_KEY")

        if unsafe_defaults:
            raise RuntimeError(
                f"Refusing to start with placeholder secrets in production! "
                f"Please set: {', '.join(unsafe_defaults)}"
            )

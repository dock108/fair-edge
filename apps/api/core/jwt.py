"""
Centralized JWT utilities using python-jose
Handles token creation and verification with consistent settings
"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
from core.settings import get_settings

_cfg = get_settings()


def create_token(data: dict, expires_minutes: int = 15) -> str:
    """
    Create a JWT token with expiration
    
    Args:
        data: Payload data to encode
        expires_minutes: Token lifetime in minutes
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(to_encode, _cfg.jwt_secret, algorithm=_cfg.jwt_algorithm)


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, _cfg.jwt_secret, algorithms=[_cfg.jwt_algorithm])


# Export JWTError for consistent exception handling
__all__ = ['create_token', 'verify_token', 'JWTError'] 
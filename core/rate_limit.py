"""
Rate limiting utilities with proxy-aware IP detection
"""
from slowapi import Limiter
from starlette.requests import Request


def _real_ip(request: Request) -> str:
    """
    Extract the real client IP from request, considering proxy headers
    
    Args:
        request: Starlette/FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # After ProxyHeadersMiddleware, request.client.host should contain the real IP
    return request.client.host or "unknown"


# Create limiter instance with real IP detection (headers disabled to fix 500 errors)
limiter = Limiter(
    key_func=_real_ip,
    headers_enabled=False  # Disabled to prevent slowapi response type conflicts
) 
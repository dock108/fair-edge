"""
Standardized exception handling for FairEdge application
Provides consistent error handling patterns and responses
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from core.auth import UserCtx

logger = logging.getLogger(__name__)


class FairEdgeException(Exception):
    """Base exception for FairEdge application"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DataFetchError(FairEdgeException):
    """Exception for data fetching failures"""

    def __init__(
        self,
        message: str,
        source: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "DATA_FETCH_ERROR", details)
        self.source = source


class CacheError(FairEdgeException):
    """Exception for cache-related failures"""

    def __init__(
        self,
        message: str,
        operation: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "CACHE_ERROR", details)
        self.operation = operation


class ValidationError(FairEdgeException):
    """Exception for input validation failures"""

    def __init__(
        self,
        message: str,
        field: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class AuthenticationError(FairEdgeException):
    """Exception for authentication failures"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(FairEdgeException):
    """Exception for authorization failures"""

    def __init__(
        self,
        message: str,
        required_role: str = "unknown",
        user_role: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTHZ_ERROR", details)
        self.required_role = required_role
        self.user_role = user_role


class ExceptionHandler:
    """Centralized exception handling with context-aware responses"""

    @staticmethod
    def handle_data_fetch_error(
        error: Exception, context: str = "unknown", user: Optional[UserCtx] = None
    ) -> Dict[str, Any]:
        """Handle data fetching errors with appropriate logging and user context"""
        if isinstance(error, DataFetchError):
            logger.error(
                f"Data fetch error in {context}: {error.message} (source: {error.source})",
                exc_info=True,
            )
            return {
                "error": "Data temporarily unavailable",
                "code": error.code,
                "context": context,
                "retry_after": 30,
            }

        logger.error(f"Unexpected data fetch error in {context}: {str(error)}", exc_info=True)
        return {
            "error": "Service temporarily unavailable",
            "code": "SERVICE_ERROR",
            "context": context,
            "retry_after": 60,
        }

    @staticmethod
    def handle_cache_error(error: Exception, operation: str = "unknown") -> Dict[str, Any]:
        """Handle cache errors with fallback strategies"""
        if isinstance(error, CacheError):
            # Include the original operation from the exception in the log
            # message
            if hasattr(error, "operation") and error.operation:
                logger.warning(
                    f"Cache error during {operation} (from {error.operation}): {error.message}"
                )
            else:
                logger.warning(f"Cache error during {operation}: {error.message}")
            return {
                "cache_status": "degraded",
                "fallback_active": True,
                "operation": operation,
            }

        logger.error(f"Unexpected cache error during {operation}: {str(error)}", exc_info=True)
        return {
            "cache_status": "error",
            "fallback_active": True,
            "operation": operation,
        }

    @staticmethod
    def handle_validation_error(error: Exception, context: str = "unknown") -> HTTPException:
        """Handle validation errors with detailed feedback"""
        if isinstance(error, ValidationError):
            logger.warning(f"Validation error in {context}: {error.message} (field: {error.field})")
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": error.message,
                    "code": error.code,
                    "field": error.field,
                    "context": context,
                },
            )

        logger.error(f"Unexpected validation error in {context}: {str(error)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid request",
                "code": "VALIDATION_ERROR",
                "context": context,
            },
        )

    @staticmethod
    def handle_authentication_error(error: Exception) -> HTTPException:
        """Handle authentication errors with security considerations"""
        if isinstance(error, AuthenticationError):
            logger.warning(f"Authentication failed: {error.message}")
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Authentication required", "code": error.code},
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.error(f"Unexpected authentication error: {str(error)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication failed", "code": "AUTH_ERROR"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def handle_authorization_error(error: Exception) -> HTTPException:
        """Handle authorization errors with role context"""
        if isinstance(error, AuthorizationError):
            logger.warning(
                f"Authorization failed: {error.message} "
                f"(required: {error.required_role}, user: {error.user_role})"
            )
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Insufficient permissions",
                    "code": error.code,
                    "required_role": error.required_role,
                },
            )

        logger.error(f"Unexpected authorization error: {str(error)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied", "code": "AUTHZ_ERROR"},
        )

    @staticmethod
    def handle_generic_error(
        error: Exception, context: str = "unknown", status_code: int = 500
    ) -> HTTPException:
        """Handle generic errors with comprehensive logging"""
        logger.error(f"Unexpected error in {context}: {str(error)}", exc_info=True)

        if status_code >= 500:
            # Don't expose internal error details in 5xx responses
            return HTTPException(
                status_code=status_code,
                detail={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "context": context,
                },
            )
        else:
            return HTTPException(
                status_code=status_code,
                detail={
                    "error": str(error),
                    "code": "REQUEST_ERROR",
                    "context": context,
                },
            )


# Convenience functions for common patterns
def safe_execute(func, *args, context: str = "unknown", fallback=None, **kwargs):
    """Safely execute a function with standardized error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execution failed in {context}: {str(e)}", exc_info=True)
        return fallback


async def safe_execute_async(func, *args, context: str = "unknown", fallback=None, **kwargs):
    """Safely execute an async function with standardized error handling"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe async execution failed in {context}: {str(e)}", exc_info=True)
        return fallback


def setup_exception_handlers(app):
    """Setup global exception handlers for the FastAPI app"""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled exceptions"""
        logger.error(
            f"Unhandled exception on {request.method} {request.url}: {str(exc)}",
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content=(exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}),
        )

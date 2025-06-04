"""
Response Service for standardized API responses and error handling
Updated to use new standardized exception handling patterns
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from fastapi import HTTPException

from core.auth import UserCtx
from core.exceptions import (
    ExceptionHandler,
    DataFetchError,
    ValidationError,
    safe_execute
)

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Standardized response formatting for all API endpoints"""
    
    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format successful API responses"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def error_response(
        error: str,
        code: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> HTTPException:
        """Format error responses with consistent structure"""
        error_detail = {
            "status": "error",
            "error": error,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            error_detail["details"] = details
            
        return HTTPException(status_code=status_code, detail=error_detail)
    
    @staticmethod
    def paginated_response(
        data: List[Any],
        total_count: int,
        page: int = 1,
        page_size: int = 50,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format paginated responses"""
        return ResponseFormatter.success_response(
            data=data,
            metadata={
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": page * page_size < total_count,
                    "has_previous": page > 1
                },
                **(metadata or {})
            }
        )


class APIResponseHandler:
    """High-level API response handling with error management"""
    
    def __init__(self, context: str = "unknown"):
        self.context = context
    
    def handle_data_response(self, data_func, *args, user: Optional[UserCtx] = None, **kwargs) -> Dict[str, Any]:
        """Handle data fetching with standardized error responses"""
        try:
            result = safe_execute(
                data_func, 
                *args, 
                context=f"{self.context}_data_fetch",
                fallback=None,
                **kwargs
            )
            
            if result is None:
                raise DataFetchError(
                    f"No data returned from {self.context}",
                    source=self.context
                )
            
            return ResponseFormatter.success_response(
                data=result,
                metadata={"source": self.context}
            )
            
        except Exception as e:
            error_response = ExceptionHandler.handle_data_fetch_error(e, self.context, user)
            return error_response
    
    async def handle_async_data_response(self, data_func, *args, user: Optional[UserCtx] = None, **kwargs) -> Dict[str, Any]:
        """Handle async data fetching with standardized error responses"""
        try:
            from core.exceptions import safe_execute_async
            
            result = await safe_execute_async(
                data_func,
                *args,
                context=f"{self.context}_async_data_fetch", 
                fallback=None,
                **kwargs
            )
            
            if result is None:
                raise DataFetchError(
                    f"No data returned from async {self.context}",
                    source=self.context
                )
            
            return ResponseFormatter.success_response(
                data=result,
                metadata={"source": self.context, "async": True}
            )
            
        except Exception as e:
            error_response = ExceptionHandler.handle_data_fetch_error(e, self.context, user)
            return error_response


# Legacy compatibility functions (maintaining existing API)
def format_success_response(
    data: Any = None,
    message: str = "Success",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Legacy wrapper for success responses"""
    return ResponseFormatter.success_response(data, message, metadata)


def format_error_response(
    error: str,
    code: str = "ERROR", 
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> HTTPException:
    """Legacy wrapper for error responses"""
    return ResponseFormatter.error_response(error, code, details, status_code)


def handle_data_fetch_error(error: Exception, user: Optional[UserCtx] = None) -> Dict[str, Any]:
    """Legacy wrapper for data fetch errors"""
    return ExceptionHandler.handle_data_fetch_error(error, "legacy_context", user)


def handle_authentication_error(error: Exception) -> HTTPException:
    """Legacy wrapper for authentication errors"""
    return ExceptionHandler.handle_authentication_error(error)


def handle_authorization_error(user_role: str, required_role: str) -> HTTPException:
    """Legacy wrapper for authorization errors"""
    from core.exceptions import AuthorizationError
    error = AuthorizationError(
        f"Access denied. Required role: {required_role}, user role: {user_role}",
        required_role=required_role,
        user_role=user_role
    )
    return ExceptionHandler.handle_authorization_error(error)


def format_opportunities_response(
    opportunities: List[Dict[str, Any]], 
    user_role: str,
    analytics: Optional[Dict[str, Any]] = None,
    filters_applied: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format betting opportunities response with role-based filtering
    """
    from core.config import feature_config
    
    # Apply role-based masking
    if user_role == "free":
        # Remove advanced fields for free users
        filtered_opportunities = []
        for opp in opportunities:
            filtered_opp = {k: v for k, v in opp.items() 
                            if not feature_config.should_mask_field(k, user_role)}
            filtered_opportunities.append(filtered_opp)
        opportunities = filtered_opportunities
    
    response_data = {
        "opportunities": opportunities,
        "role": user_role,
        "total_count": len(opportunities)
    }
    
    if analytics:
        # Apply same role-based filtering to analytics
        if user_role == "free":
            filtered_analytics = {k: v for k, v in analytics.items() 
                                  if not feature_config.should_mask_field(k, user_role)}
        else:
            filtered_analytics = analytics
        response_data["analytics"] = filtered_analytics
    
    metadata = {
        "features": feature_config.get_user_features(user_role)
    }
    
    if filters_applied:
        metadata["filters_applied"] = filters_applied
    
    return ResponseFormatter.success_response(
        data=response_data,
        metadata=metadata
    )


def validate_request_params(params: Dict[str, Any], required: List[str] = None, context: str = "request") -> None:
    """
    Validate request parameters and raise appropriate exceptions
    """
    required = required or []
    
    for param in required:
        if param not in params or params[param] is None:
            raise ValidationError(
                f"Missing required parameter: {param}",
                field=param,
                details={"required_params": required, "provided_params": list(params.keys())}
            )
    
    # Additional validation can be added here
    logger.debug(f"Request validation passed for {context}: {list(params.keys())}")


# Convenience class for endpoint handlers
class EndpointHandler:
    """Convenience wrapper for common endpoint patterns"""
    
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.response_handler = APIResponseHandler(endpoint_name)
    
    def validate_and_execute(
        self,
        data_func,
        request_params: Dict[str, Any],
        required_params: List[str] = None,
        user: Optional[UserCtx] = None
    ) -> Dict[str, Any]:
        """Validate parameters and execute data function with error handling"""
        try:
            # Validate request parameters
            validate_request_params(request_params, required_params, self.endpoint_name)
            
            # Execute data function
            return self.response_handler.handle_data_response(
                data_func,
                **request_params,
                user=user
            )
            
        except ValidationError as e:
            raise ExceptionHandler.handle_validation_error(e, self.endpoint_name)
        except Exception as e:
            raise ExceptionHandler.handle_generic_error(e, self.endpoint_name)


# Legacy compatibility classes and functions
class APIResponse:
    """Legacy compatibility class - redirects to new ResponseFormatter"""
    
    @staticmethod
    def success(data: Dict[str, Any], 
                user: Optional[UserCtx] = None,
                message: Optional[str] = None) -> Dict[str, Any]:
        """Legacy success method"""
        return ResponseFormatter.success_response(
            data=data,
            message=message or "Success",
            metadata={"user": user.role if user else None}
        )
    
    @staticmethod
    def error(message: str, 
              error_code: str = "GENERAL_ERROR",
              details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy error method - returns dict instead of HTTPException for compatibility"""
        return {
            "status": "error",
            "error": {
                "code": error_code,
                "message": message,
                "details": details
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def opportunities_response(opportunities: List[Dict[str, Any]],
                               analytics: Dict[str, Any],
                               user: UserCtx,
                               data_source: str = "cache",
                               last_update: Optional[str] = None,
                               filters_applied: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy opportunities response method"""
        response_data = {
            "opportunities": opportunities,
            "analytics": analytics,
            "data_source": data_source,
            "last_update": last_update or datetime.now().isoformat()
        }
        
        if filters_applied:
            response_data["filters_applied"] = filters_applied
        
        return APIResponse.success(response_data, user)


class ErrorHandler:
    """Legacy compatibility class - redirects to new ExceptionHandler"""
    
    @staticmethod
    def handle_data_fetch_error(error: Exception, user: Optional[UserCtx] = None) -> Dict[str, Any]:
        """Legacy data fetch error handler"""
        # Log the error using the new handler (but don't use the response)
        ExceptionHandler.handle_data_fetch_error(error, "legacy_context", user)
        
        # Convert to legacy format for backwards compatibility
        fallback_data = {
            "opportunities": [],
            "analytics": {},
            "data_source": "error",
            "last_update": datetime.now().isoformat(),
            "error_message": "Unable to retrieve opportunities data"
        }
        
        return APIResponse.success(fallback_data, user, "Service temporarily unavailable")
    
    @staticmethod
    def handle_authentication_error(error: Exception) -> HTTPException:
        """Legacy authentication error handler"""
        return ExceptionHandler.handle_authentication_error(error)
    
    @staticmethod
    def handle_authorization_error(user_role: str, required_role: str) -> HTTPException:
        """Legacy authorization error handler"""
        return handle_authorization_error(user_role, required_role) 
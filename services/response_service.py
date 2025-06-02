"""
Response Service for standardizing API response patterns
Centralizes response formatting that was duplicated across endpoints
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import HTTPException
import logging

from core.auth import UserCtx

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Standardized API response builder
    Ensures consistent response format across all endpoints
    """
    
    @staticmethod
    def success(data: Dict[str, Any], 
                user: Optional[UserCtx] = None,
                message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a successful API response
        
        Args:
            data: The main response data
            user: User context for metadata
            message: Optional success message
        """
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        if user:
            from services.user_service import create_user_response_metadata
            response.update(create_user_response_metadata(user))
        
        if message:
            response["message"] = message
            
        return response
    
    @staticmethod
    def error(message: str, 
              error_code: str = "GENERAL_ERROR",
              details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an error API response
        
        Args:
            message: Error message
            error_code: Error code for client handling
            details: Additional error details
        """
        response = {
            "status": "error",
            "error": {
                "code": error_code,
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            response["error"]["details"] = details
            
        return response
    
    @staticmethod
    def opportunities_response(opportunities: List[Dict[str, Any]],
                               analytics: Dict[str, Any],
                               user: UserCtx,
                               data_source: str = "cache",
                               last_update: Optional[str] = None,
                               filters_applied: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Standardized opportunities response format
        Used by multiple endpoints that return opportunities
        """
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
    """
    Centralized error handling with consistent error responses
    """
    
    @staticmethod
    def handle_data_fetch_error(error: Exception, user: Optional[UserCtx] = None) -> Dict[str, Any]:
        """Handle data fetching errors with fallback response"""
        logger.error(f"Data fetch error: {error}")
        
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
        """Handle authentication errors consistently"""
        logger.warning(f"Authentication error: {error}")
        return HTTPException(status_code=401, detail="Authentication required")
    
    @staticmethod
    def handle_authorization_error(user_role: str, required_role: str) -> HTTPException:
        """Handle authorization errors consistently"""
        logger.warning(f"Authorization error: {user_role} tried to access {required_role} resource")
        return HTTPException(
            status_code=403, 
            detail=f"Insufficient permissions. Required: {required_role}, Current: {user_role}"
        )


def create_paginated_response(
    items: List[Any],
    total_count: int,
    page: int = 1,
    page_size: int = 50,
    user: Optional[UserCtx] = None
) -> Dict[str, Any]:
    """
    Create a paginated response format
    For future use when pagination is needed
    """
    total_pages = (total_count + page_size - 1) // page_size
    
    pagination_data = {
        "items": items,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_count,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    }
    
    return APIResponse.success(pagination_data, user)


def create_filtered_opportunities_response(
    filtered_response: Dict[str, Any],
    analytics: Dict[str, Any],
    user: UserCtx,
    data_source: str = "cache",
    last_update: Optional[str] = None,
    filters_applied: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized response for filtered opportunities
    This is the most common response format in the application
    """
    opportunities = filtered_response.get("opportunities", [])
    
    response_data = {
        "total": filtered_response.get("total_available", 0),
        "shown": filtered_response.get("shown", 0),
        "opportunities": opportunities,
        "analytics": analytics,
        "data_source": data_source,
        "last_update": last_update or datetime.now().isoformat(),
        "truncated": filtered_response.get("truncated", False),
        "role_metadata": {
            "role": filtered_response.get("role", user.role),
            "features": filtered_response.get("features", {}),
            "limit": filtered_response.get("limit")
        }
    }
    
    if filters_applied:
        response_data["filters_applied"] = filters_applied
    
    return APIResponse.success(response_data, user)


def create_dashboard_template_context(
    request: Any,
    user: UserCtx,
    filtered_response: Dict[str, Any],
    analytics: Dict[str, Any],
    settings: Any,
    sports_supported: List[str],
    admin_mode: bool = False,
    debug_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized dashboard template context
    Eliminates duplication in page endpoints that show dashboard data
    """
    # Apply filters from query parameters
    sport_filter = request.query_params.get('sport', '').strip()
    market_filter = request.query_params.get('market', '').strip()
    
    filtered_opportunities = filtered_response.get('opportunities', [])
    
    # Apply client-side filters if needed
    if sport_filter:
        filtered_opportunities = [
            op for op in filtered_opportunities 
            if sport_filter.lower() in op.get('sport', '').lower()
        ]
    
    if market_filter:
        filtered_opportunities = [
            op for op in filtered_opportunities 
            if market_filter.lower() in op.get('market', '').lower()
        ]
    
    # Calculate UI analytics
    ui_analytics = {
        'total_opportunities': len(filtered_opportunities),
        'positive_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) > 0]),
        'high_ev_count': len([op for op in filtered_opportunities if op.get('ev_percentage', 0) >= 4.5]),
        'max_ev_percentage': round(max([op.get('ev_percentage', 0) for op in filtered_opportunities], default=0), 2)
    }
    
    # Base context
    context = {
        "request": request,
        "settings": settings,
        "user": user,
        "user_role": user.role,
        "is_guest": getattr(user, 'id', None) == "guest",
        "opportunities": filtered_opportunities,
        "analytics": ui_analytics,
        "admin_mode": admin_mode,
        "filter_applied": bool(sport_filter or market_filter),
        "current_sport": sport_filter,
        "current_market": market_filter,
        "page_title": "Live Betting Dashboard - Sports +EV Analysis",
        "role_metadata": {
            "truncated": filtered_response.get('truncated', False),
            "limit": filtered_response.get('limit'),
            "total_available": filtered_response.get('total_available', 0),
            "shown": filtered_response.get('shown', 0),
            "features": filtered_response.get('features', {})
        },
        "sports_supported": sports_supported
    }
    
    # Add debug data if provided
    if debug_data:
        context.update(debug_data)
    
    return context 
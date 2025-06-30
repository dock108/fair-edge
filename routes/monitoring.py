"""
Monitoring and health check endpoints for the betting system
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from services.persistence_monitoring import persistence_monitor, log_performance_metrics
from db import get_database_status
from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    """
    try:
        db_status = await get_database_status()
        persistence_health = persistence_monitor.check_health()
        
        overall_status = "healthy"
        if (not db_status.get("overall_status") == "healthy" or 
            persistence_health.get("status") != "healthy"):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "persistence": {
                "status": persistence_health["status"],
                "recent_operations": len(persistence_monitor.operation_history),
                "recent_errors": len(persistence_monitor.error_history)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/persistence/performance")
async def persistence_performance(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get detailed persistence performance metrics
    Requires authentication
    """
    try:
        # Log current metrics
        log_performance_metrics()
        
        return persistence_monitor.get_performance_summary()
    except Exception as e:
        logger.error(f"Failed to get persistence performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/persistence/health")
async def persistence_health(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get detailed persistence health check
    Requires authentication
    """
    try:
        return persistence_monitor.check_health()
    except Exception as e:
        logger.error(f"Failed to get persistence health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/persistence/errors")
async def persistence_errors(limit: int = 20, current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get recent persistence errors
    Requires authentication
    """
    try:
        return {
            "errors": persistence_monitor.get_recent_errors(limit),
            "total_errors_24h": len(persistence_monitor.error_history)
        }
    except Exception as e:
        logger.error(f"Failed to get persistence errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error data")


@router.get("/persistence/metrics/export")
async def export_metrics(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Export all persistence metrics for external monitoring
    Requires authentication
    """
    try:
        return persistence_monitor.export_metrics()
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")
"""
Persistence Monitoring Service

Provides monitoring, metrics, and performance tracking for the betting opportunities
persistence system.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class PersistenceMonitor:
    """Monitor persistence performance and health"""
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.operation_history = deque(maxlen=max_history)
        self.error_history = deque(maxlen=max_history)
        self.performance_metrics = defaultdict(list)
        self.start_time = datetime.now()
        
    def record_operation(self, operation_type: str, duration_ms: int, 
                        success: bool, details: Dict[str, Any] = None):
        """Record a persistence operation for monitoring"""
        record = {
            "timestamp": datetime.now(),
            "operation_type": operation_type,
            "duration_ms": duration_ms,
            "success": success,
            "details": details or {}
        }
        
        self.operation_history.append(record)
        
        # Track performance metrics
        self.performance_metrics[operation_type].append({
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": record["timestamp"]
        })
        
        # Keep only recent metrics (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.performance_metrics[operation_type] = [
            m for m in self.performance_metrics[operation_type] 
            if m["timestamp"] > cutoff_time
        ]
        
        if not success:
            self.error_history.append(record)
            
        logger.debug(f"Recorded {operation_type}: {duration_ms}ms, success={success}")
    
    def record_batch_operation(self, result: Dict[str, Any]):
        """Record a batch persistence operation result"""
        self.record_operation(
            operation_type="batch_save",
            duration_ms=result.get("processing_time_ms", 0),
            success=result.get("status") == "success",
            details={
                "bets_created": result.get("bets_created", 0),
                "bets_updated": result.get("bets_updated", 0),
                "offers_created": result.get("offers_created", 0),
                "error_count": len(result.get("errors", [])),
                "total_opportunities": result.get("total_opportunities", 0),
                "source": result.get("source", "unknown")
            }
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the last 24 hours"""
        summary = {
            "monitoring_period_hours": 24,
            "total_operations": len(self.operation_history),
            "total_errors": len(self.error_history),
            "operations_by_type": {},
            "overall_success_rate": 0.0,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }
        
        if not self.operation_history:
            return summary
        
        # Calculate success rate
        successful_ops = sum(1 for op in self.operation_history if op["success"])
        summary["overall_success_rate"] = successful_ops / len(self.operation_history) * 100
        
        # Analyze by operation type
        for op_type, metrics in self.performance_metrics.items():
            if not metrics:
                continue
                
            durations = [m["duration_ms"] for m in metrics]
            successes = [m["success"] for m in metrics]
            
            summary["operations_by_type"][op_type] = {
                "count": len(metrics),
                "success_rate": sum(successes) / len(successes) * 100,
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": self._percentile(durations, 95)
            }
        
        return summary
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error details"""
        recent_errors = list(self.error_history)[-limit:]
        return [
            {
                "timestamp": error["timestamp"].isoformat(),
                "operation_type": error["operation_type"],
                "duration_ms": error["duration_ms"],
                "details": error["details"]
            }
            for error in recent_errors
        ]
    
    def check_health(self) -> Dict[str, Any]:
        """Check overall health of persistence system"""
        health = {
            "status": "healthy",
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        # Check recent operation success rate
        recent_ops = [op for op in self.operation_history 
                     if op["timestamp"] > datetime.now() - timedelta(minutes=30)]
        
        if recent_ops:
            recent_success_rate = sum(1 for op in recent_ops if op["success"]) / len(recent_ops) * 100
            health["checks"]["recent_success_rate"] = {
                "value": recent_success_rate,
                "status": "healthy" if recent_success_rate >= 95 else "warning" if recent_success_rate >= 85 else "error"
            }
            
            if recent_success_rate < 95:
                health["warnings"].append(f"Recent success rate below 95%: {recent_success_rate:.1f}%")
            if recent_success_rate < 85:
                health["errors"].append(f"Recent success rate critically low: {recent_success_rate:.1f}%")
                health["status"] = "error"
        else:
            health["checks"]["recent_operations"] = {
                "value": 0,
                "status": "warning"
            }
            health["warnings"].append("No recent operations detected")
        
        # Check average performance
        if "batch_save" in self.performance_metrics:
            batch_metrics = self.performance_metrics["batch_save"]
            if batch_metrics:
                avg_duration = sum(m["duration_ms"] for m in batch_metrics) / len(batch_metrics)
                health["checks"]["avg_batch_duration"] = {
                    "value": avg_duration,
                    "status": "healthy" if avg_duration < 5000 else "warning" if avg_duration < 10000 else "error"
                }
                
                if avg_duration > 10000:
                    health["errors"].append(f"Average batch duration too high: {avg_duration:.0f}ms")
                    health["status"] = "error"
                elif avg_duration > 5000:
                    health["warnings"].append(f"Average batch duration elevated: {avg_duration:.0f}ms")
        
        # Overall status
        if health["errors"]:
            health["status"] = "error"
        elif health["warnings"]:
            health["status"] = "warning"
        
        return health
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external monitoring systems"""
        return {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": self.get_performance_summary(),
            "health_check": self.check_health(),
            "recent_errors": self.get_recent_errors(5),
            "system_info": {
                "monitor_start_time": self.start_time.isoformat(),
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "max_history_size": self.max_history,
                "current_history_size": len(self.operation_history)
            }
        }


# Global monitor instance
persistence_monitor = PersistenceMonitor()


def log_performance_metrics():
    """Log current performance metrics"""
    try:
        summary = persistence_monitor.get_performance_summary()
        health = persistence_monitor.check_health()
        
        logger.info(f"Persistence Performance Summary:")
        logger.info(f"  Total Operations (24h): {summary['total_operations']}")
        logger.info(f"  Success Rate: {summary['overall_success_rate']:.1f}%")
        logger.info(f"  Health Status: {health['status']}")
        
        if summary.get("operations_by_type", {}).get("batch_save"):
            batch_stats = summary["operations_by_type"]["batch_save"]
            logger.info(f"  Batch Save Performance:")
            logger.info(f"    Count: {batch_stats['count']}")
            logger.info(f"    Avg Duration: {batch_stats['avg_duration_ms']:.0f}ms")
            logger.info(f"    P95 Duration: {batch_stats['p95_duration_ms']:.0f}ms")
            logger.info(f"    Success Rate: {batch_stats['success_rate']:.1f}%")
        
        # Log warnings and errors
        for warning in health.get("warnings", []):
            logger.warning(f"Persistence Warning: {warning}")
        for error in health.get("errors", []):
            logger.error(f"Persistence Error: {error}")
            
    except Exception as e:
        logger.error(f"Failed to log performance metrics: {e}")
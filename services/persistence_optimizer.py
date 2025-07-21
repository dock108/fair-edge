"""
Persistence Performance Optimizer

Provides utilities to optimize database persistence performance based on
monitoring data and system load.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from services.persistence_monitoring import persistence_monitor

logger = logging.getLogger(__name__)


class PersistenceOptimizer:
    """Optimize persistence performance based on monitoring data"""

    def __init__(self):
        self.last_optimization = None
        self.optimization_interval = timedelta(hours=1)  # Optimize once per hour

    def should_optimize(self) -> bool:
        """Check if optimization should run"""
        if not self.last_optimization:
            return True
        return datetime.now() - self.last_optimization > self.optimization_interval

    def get_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on performance history"""
        try:
            batch_metrics = persistence_monitor.performance_metrics.get("batch_save", [])
            if not batch_metrics:
                return 100  # Default batch size

            # Analyze recent performance
            recent_metrics = [
                m for m in batch_metrics if m["timestamp"] > datetime.now() - timedelta(hours=2)
            ]

            if not recent_metrics:
                return 100

            avg_duration = sum(m["duration_ms"] for m in recent_metrics) / len(recent_metrics)
            success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)

            # Adjust batch size based on performance
            base_size = 100

            # If duration is high, reduce batch size
            if avg_duration > 5000:  # More than 5 seconds
                base_size = 50
            elif avg_duration > 2000:  # More than 2 seconds
                base_size = 75
            elif avg_duration < 1000:  # Less than 1 second
                base_size = 150

            # If success rate is low, reduce batch size for stability
            if success_rate < 0.9:
                base_size = min(base_size, 50)
            elif success_rate < 0.95:
                base_size = min(base_size, 75)

            logger.info(
                f"Optimal batch size calculated: {base_size} (avg_duration={avg_duration:.0f}ms, success_rate={success_rate:.2f})"
            )
            return base_size

        except Exception as e:
            logger.error(f"Failed to calculate optimal batch size: {e}")
            return 100  # Safe default

    def get_performance_recommendations(self) -> Dict[str, Any]:
        """Get performance optimization recommendations"""
        try:
            recommendations: Dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "recommendations": [],
                "metrics_analyzed": False,
            }

            # Analyze recent performance
            health = persistence_monitor.check_health()
            summary = persistence_monitor.get_performance_summary()

            recommendations["metrics_analyzed"] = True

            # Check success rate
            if health["status"] == "error":
                recommendations["recommendations"].append(
                    {
                        "type": "critical",
                        "category": "reliability",
                        "message": "Critical persistence issues detected",
                        "action": "Check error logs and database connectivity",
                        "priority": "high",
                    }
                )

            # Check performance
            batch_stats = summary.get("operations_by_type", {}).get("batch_save")
            if batch_stats:
                avg_duration = batch_stats.get("avg_duration_ms", 0)
                p95_duration = batch_stats.get("p95_duration_ms", 0)

                if avg_duration > 5000:
                    recommendations["recommendations"].append(
                        {
                            "type": "performance",
                            "category": "latency",
                            "message": f"High average batch duration: {avg_duration:.0f}ms",
                            "action": "Consider reducing batch size or optimizing database queries",
                            "priority": "medium",
                        }
                    )

                if p95_duration > 10000:
                    recommendations["recommendations"].append(
                        {
                            "type": "performance",
                            "category": "latency",
                            "message": f"High P95 batch duration: {p95_duration:.0f}ms",
                            "action": "Investigate slow queries and database performance",
                            "priority": "medium",
                        }
                    )

                success_rate = batch_stats.get("success_rate", 100)
                if success_rate < 95:
                    recommendations["recommendations"].append(
                        {
                            "type": "reliability",
                            "category": "errors",
                            "message": f"Low success rate: {success_rate:.1f}%",
                            "action": "Review error logs and implement retry logic",
                            "priority": "high",
                        }
                    )

            # Check operation frequency
            if summary["total_operations"] == 0:
                recommendations["recommendations"].append(
                    {
                        "type": "monitoring",
                        "category": "activity",
                        "message": "No persistence operations detected",
                        "action": "Verify Celery tasks are running and processing data",
                        "priority": "high",
                    }
                )

            # Resource utilization recommendations
            if len(persistence_monitor.operation_history) > 800:  # Close to max capacity
                recommendations["recommendations"].append(
                    {
                        "type": "capacity",
                        "category": "monitoring",
                        "message": "Monitoring history approaching capacity",
                        "action": "Consider increasing monitoring buffer size",
                        "priority": "low",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate performance recommendations: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "recommendations": [],
                "error": str(e),
                "metrics_analyzed": False,
            }

    def optimize_if_needed(self) -> Optional[Dict[str, Any]]:
        """Run optimization if needed and return results"""
        if not self.should_optimize():
            return None

        try:
            recommendations = self.get_performance_recommendations()
            optimal_batch_size = self.get_optimal_batch_size()

            self.last_optimization = datetime.now()

            optimization_result = {
                "timestamp": self.last_optimization.isoformat(),
                "optimal_batch_size": optimal_batch_size,
                "recommendations": recommendations,
                "next_optimization": (
                    self.last_optimization + self.optimization_interval
                ).isoformat(),
            }

            logger.info(
                f"Persistence optimization completed: batch_size={optimal_batch_size}, recommendations={len(recommendations.get('recommendations', []))}"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "optimal_batch_size": 100,  # Safe fallback
            }


# Global optimizer instance
persistence_optimizer = PersistenceOptimizer()

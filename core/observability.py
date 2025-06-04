"""
Observability configuration for bet-intel application
Integrates Prometheus metrics and Sentry error tracking
"""
import os
from typing import Dict, Any, Optional
import time

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from core.logging import get_logger

logger = get_logger(__name__)

# Custom Prometheus metrics for bet-intel specific monitoring
OPPORTUNITY_METRICS = {
    'opportunities_processed': Counter(
        'bet_intel_opportunities_processed_total',
        'Total number of betting opportunities processed',
        ['sport', 'market_type']
    ),
    'ev_distribution': Histogram(
        'bet_intel_ev_percentage_distribution',
        'Distribution of EV percentages found',
        buckets=[0, 1, 2.5, 4.5, 7.5, 10, 15, 20, float('inf')]
    ),
    'cache_operations': Counter(
        'bet_intel_cache_operations_total',
        'Redis cache operations',
        ['operation', 'result']
    ),
    'active_opportunities': Gauge(
        'bet_intel_opportunities_active',
        'Current number of active opportunities',
        ['ev_tier']
    ),
    'api_requests_by_role': Counter(
        'bet_intel_api_requests_by_role_total',
        'API requests by user role',
        ['role', 'endpoint', 'status_code']
    ),
    'data_refresh_duration': Histogram(
        'bet_intel_data_refresh_seconds',
        'Time taken for data refresh operations',
        ['source']
    ),
    'database_query_duration': Histogram(
        'bet_intel_db_query_seconds',
        'Database query execution time',
        ['query_type', 'table']
    )
}


class ObservabilityManager:
    """Centralized observability management"""
    
    def __init__(self):
        self.sentry_enabled = False
        self.prometheus_enabled = False
        self.instrumentator = None
    
    def setup_sentry(self) -> bool:
        """Initialize Sentry error tracking"""
        sentry_dsn = os.getenv("SENTRY_DSN")
        
        if not sentry_dsn:
            logger.info("Sentry DSN not configured, skipping Sentry setup")
            return False
        
        environment = os.getenv("APP_ENV", "development")
        
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=True),
                    CeleryIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                ],
                # Custom error filtering
                before_send=self._sentry_filter_errors,
                # Set release from environment
                release=os.getenv("APP_VERSION", "unknown"),
                # Add custom tags
                default_integrations=True,
            )
            
            # Add user context
            sentry_sdk.set_tag("service", "bet-intel")
            sentry_sdk.set_tag("component", "api")
            
            logger.info("Sentry initialized successfully", 
                       environment=environment,
                       traces_sample_rate=os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
            
            self.sentry_enabled = True
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Sentry", error=str(e))
            return False
    
    def _sentry_filter_errors(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter out noisy errors from Sentry"""
        # Skip common health check errors
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            if 'health' in str(exc_value).lower():
                return None
        
        # Skip rate limiting errors (they're expected)
        if event.get('exception', {}).get('values'):
            for exc in event['exception']['values']:
                if 'rate limit' in exc.get('type', '').lower():
                    return None
        
        return event
    
    def setup_prometheus(self, app=None) -> bool:
        """Initialize Prometheus metrics"""
        try:
            # Create instrumentator
            self.instrumentator = Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True,
                should_respect_env_var=True,
                should_instrument_requests_inprogress=True,
                excluded_handlers=["/health", "/metrics"],
                env_var_name="ENABLE_METRICS",
                inprogress_name="bet_intel_requests_inprogress",
                inprogress_labels=True,
            )
            
            if app:
                # Instrument the FastAPI app
                self.instrumentator.instrument(app)
                
                # Expose metrics endpoint with gzip compression - Phase 3.5
                self.instrumentator.expose(
                    app, 
                    endpoint="/metrics",
                    include_in_schema=False,
                    should_gzip=True,  # Enable gzip compression
                    tags=["monitoring"]
                )
            
            # Register custom metrics
            self._register_custom_metrics()
            
            logger.info("Prometheus metrics initialized successfully")
            self.prometheus_enabled = True
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Prometheus", error=str(e))
            return False
    
    def _register_custom_metrics(self):
        """Register custom Prometheus metrics"""
        # Metrics are already defined globally, just log their registration
        logger.info("Custom Prometheus metrics registered", 
                   metrics_count=len(OPPORTUNITY_METRICS))
    
    def start_metrics_server(self, port: int = 8001):
        """Start standalone Prometheus metrics server"""
        try:
            start_http_server(port)
            logger.info("Prometheus metrics server started", port=port)
        except Exception as e:
            logger.error("Failed to start metrics server", error=str(e), port=port)
    
    def record_opportunity_processed(self, sport: str, market_type: str, ev_percentage: float):
        """Record an opportunity being processed"""
        if not self.prometheus_enabled:
            return
        
        try:
            # Count the opportunity
            OPPORTUNITY_METRICS['opportunities_processed'].labels(
                sport=sport, 
                market_type=market_type
            ).inc()
            
            # Record EV distribution
            OPPORTUNITY_METRICS['ev_distribution'].observe(ev_percentage)
            
            # Update active opportunities gauge by EV tier
            ev_tier = self._get_ev_tier(ev_percentage)
            OPPORTUNITY_METRICS['active_opportunities'].labels(ev_tier=ev_tier).inc()
            
        except Exception as e:
            logger.warning("Failed to record opportunity metrics", error=str(e))
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        if not self.prometheus_enabled:
            return
        
        try:
            OPPORTUNITY_METRICS['cache_operations'].labels(
                operation=operation,
                result=result
            ).inc()
        except Exception as e:
            logger.warning("Failed to record cache metrics", error=str(e))
    
    def record_api_request(self, role: str, endpoint: str, status_code: int):
        """Record API request metrics by user role"""
        if not self.prometheus_enabled:
            return
        
        try:
            OPPORTUNITY_METRICS['api_requests_by_role'].labels(
                role=role,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
        except Exception as e:
            logger.warning("Failed to record API request metrics", error=str(e))
    
    def record_refresh_duration(self, source: str, duration_seconds: float):
        """Record data refresh operation duration"""
        if not self.prometheus_enabled:
            return
        
        try:
            OPPORTUNITY_METRICS['data_refresh_duration'].labels(source=source).observe(duration_seconds)
        except Exception as e:
            logger.warning("Failed to record refresh duration", error=str(e))
    
    def record_db_query_duration(self, query_type: str, table: str, duration_seconds: float):
        """Record database query duration"""
        if not self.prometheus_enabled:
            return
        
        try:
            OPPORTUNITY_METRICS['database_query_duration'].labels(
                query_type=query_type,
                table=table
            ).observe(duration_seconds)
        except Exception as e:
            logger.warning("Failed to record DB query duration", error=str(e))
    
    def _get_ev_tier(self, ev_percentage: float) -> str:
        """Classify EV percentage into tiers"""
        if ev_percentage >= 4.5:
            return "excellent"
        elif ev_percentage >= 2.5:
            return "high"
        elif ev_percentage > 0:
            return "positive"
        else:
            return "neutral"
    
    def capture_exception(self, error: Exception, **context):
        """Capture exception with Sentry"""
        if not self.sentry_enabled:
            logger.error("Exception occurred", error=str(error), **context)
            return
        
        # Add context to Sentry
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
            
            sentry_sdk.capture_exception(error)
    
    def capture_message(self, message: str, level: str = "info", **context):
        """Capture message with Sentry"""
        if not self.sentry_enabled:
            logger.log(getattr(logger, level, logger.info), message, **context)
            return
        
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
            
            sentry_sdk.capture_message(message, level)


# Global observability manager instance
observability = ObservabilityManager()


def setup_observability(app=None) -> ObservabilityManager:
    """Setup complete observability stack"""
    logger.info("Setting up observability stack...")
    
    # Setup Sentry
    sentry_ok = observability.setup_sentry()
    
    # Setup Prometheus
    prometheus_ok = observability.setup_prometheus(app)
    
    logger.info("Observability setup complete", 
               sentry_enabled=sentry_ok,
               prometheus_enabled=prometheus_ok)
    
    return observability


# Utility decorators for easy instrumentation
def track_time(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to track execution time"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name in OPPORTUNITY_METRICS:
                    if labels:
                        OPPORTUNITY_METRICS[metric_name].labels(**labels).observe(duration)
                    else:
                        OPPORTUNITY_METRICS[metric_name].observe(duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name in OPPORTUNITY_METRICS:
                    if labels:
                        OPPORTUNITY_METRICS[metric_name].labels(**labels).observe(duration)
                    else:
                        OPPORTUNITY_METRICS[metric_name].observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 
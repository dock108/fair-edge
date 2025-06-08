"""
Admin and system maintenance tasks
Domain-specific tasks for health checks, monitoring, and system maintenance
"""

import logging
from datetime import datetime

from celery import shared_task

from services.redis_cache import health_check as redis_health_check
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="admin.health_check",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    soft_time_limit=30,  # 30 seconds
)
def health_check(self):
    """
    Comprehensive system health check task
    Checks Redis, database, and other critical components
    """
    try:
        logger.info("🔍 Starting system health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check Redis
        try:
            redis_status = redis_health_check()
            health_status['components']['redis'] = {
                'status': 'healthy' if redis_status else 'unhealthy',
                'details': redis_status
            }
            logger.info(f"✅ Redis health: {'OK' if redis_status else 'FAILED'}")
        except Exception as e:
            health_status['components']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            logger.error(f"❌ Redis health check failed: {e}")
        
        # Check database
        try:
            from db import check_database_connection
            import asyncio
            db_status = asyncio.run(check_database_connection())
            health_status['components']['database'] = {
                'status': 'healthy' if db_status else 'unhealthy'
            }
            logger.info(f"✅ Database health: {'OK' if db_status else 'FAILED'}")
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            logger.error(f"❌ Database health check failed: {e}")
        
        # Check configuration
        config_issues = []
        if not settings.odds_api_key:
            config_issues.append("Missing ODDS_API_KEY")
        if not settings.db_connection_string:
            config_issues.append("Missing DB_CONNECTION_STRING")
        
        health_status['components']['configuration'] = {
            'status': 'healthy' if not config_issues else 'warning',
            'issues': config_issues
        }
        
        # Determine overall status
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if 'unhealthy' in component_statuses:
            health_status['overall_status'] = 'unhealthy'
        elif 'warning' in component_statuses:
            health_status['overall_status'] = 'warning'
        
        logger.info(f"✅ Health check completed: {health_status['overall_status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check task failed: {e}")
        raise


@shared_task(
    bind=True,
    name="admin.system_stats",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2}
)
def get_system_stats(self):
    """Get system statistics and metrics"""
    try:
        import redis
        from services.celery_app import celery_app
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'celery': {},
            'redis': {},
            'application': {}
        }
        
        # Celery stats
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            stats['celery'] = {
                'active_tasks': len(active_tasks) if active_tasks else 0,
                'scheduled_tasks': len(scheduled_tasks) if scheduled_tasks else 0,
                'workers': list(active_tasks.keys()) if active_tasks else []
            }
        except Exception as e:
            stats['celery']['error'] = str(e)
        
        # Redis stats
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_info = redis_client.info()
            stats['redis'] = {
                'connected_clients': redis_info.get('connected_clients', 0),
                'used_memory_human': redis_info.get('used_memory_human', 'unknown'),
                'total_commands_processed': redis_info.get('total_commands_processed', 0)
            }
        except Exception as e:
            stats['redis']['error'] = str(e)
        
        # Application stats
        stats['application'] = {
            'environment': settings.app_env,
            'debug_mode': settings.debug or settings.debug_mode,
            'refresh_interval': settings.refresh_interval_minutes
        }
        
        logger.info("✅ System stats collected successfully")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to collect system stats: {e}")
        raise 
"""
Celery task definitions for bet-intel
Background tasks for data processing and real-time updates
"""

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from celery import shared_task, Celery
from celery.signals import worker_shutdown

from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities
from services.redis_cache import store_ev_data, store_analytics_data, health_check as redis_health_check
from core.constants import CACHE_KEYS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of supported sports (can be expanded)
SPORTS_SUPPORTED = [
    'americanfootball_nfl',
    'basketball_nba', 
    'baseball_mlb',
    'icehockey_nhl'
]

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery with timeout configurations
celery_app = Celery(
    'bet_intel_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['services.tasks']
)

# Configure Celery for graceful shutdown
celery_app.conf.update(
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    worker_disable_rate_limits=True,
    
    # Shutdown settings
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Graceful shutdown
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_reject_on_worker_lost=True,
)

# Global cleanup flags
is_shutting_down = False
active_tasks = set()

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal"""
    global is_shutting_down
    is_shutting_down = True
    logger.info("🛑 Celery worker shutdown signal received")
    
    # Cancel active tasks
    for task_id in list(active_tasks):
        try:
            celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')
            logger.info(f"   Cancelled task: {task_id}")
        except Exception as e:
            logger.warning(f"   Error cancelling task {task_id}: {e}")
    
    active_tasks.clear()
    logger.info("✅ Celery cleanup completed")

def cleanup_celery():
    """Cleanup Celery workers gracefully"""
    global is_shutting_down, active_tasks
    is_shutting_down = True
    
    logger.info("🔧 Cleaning up Celery workers...")
    
    try:
        # Cancel active tasks
        for task_id in list(active_tasks):
            try:
                celery_app.control.revoke(task_id, terminate=True)
                active_tasks.discard(task_id)
            except Exception as e:
                logger.warning(f"Failed to cancel task {task_id}: {e}")
        
        # Stop workers gracefully (if we're the worker process)
        try:
            celery_app.control.shutdown()
        except Exception:
            pass  # This might fail if we're not a worker
        
        logger.info("✅ Celery workers cleaned up")
        
    except Exception as e:
        logger.error(f"Error during Celery cleanup: {e}")

# Register cleanup function
try:
    import sys
    if 'app' in sys.modules:
        from app import register_cleanup
        register_cleanup(cleanup_celery)
except ImportError:
    pass

@shared_task(
    bind=True,
    name="refresh_odds_data",
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_kwargs={"max_retries": 5},
    soft_time_limit=20 * 60,  # 20 minutes soft limit
    time_limit=25 * 60,       # 25 minutes hard limit
)
def refresh_odds_data(self):
    """
    Background task to refresh odds data and process EV opportunities with fault tolerance.
    
    This task:
    1. Fetches fresh data from The Odds API for all supported sports
    2. Processes EV opportunities with role-based segmentation
    3. Stores results in Redis with appropriate cache keys
    4. Implements automatic retries with exponential backoff
    """
    start_time = time.perf_counter()
    all_opportunities = []
    
    try:
        logger.info("🚀 Celery task started: Refreshing odds data for all sports")
        
        # Update task state to show progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0, 
                'total': len(SPORTS_SUPPORTED) + 2, 
                'status': 'Starting odds refresh...',
                'sports': SPORTS_SUPPORTED
            }
        )
        
        # Process each sport individually for better fault tolerance
        successful_sports = []
        failed_sports = []
        
        for i, sport in enumerate(SPORTS_SUPPORTED, 1):
            try:
                logger.info(f"📊 Processing sport: {sport}")
                
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(SPORTS_SUPPORTED) + 2,
                        'status': f'Fetching {sport} odds...',
                        'sport': sport
                    }
                )
                
                # Fetch raw odds for this sport
                raw_data = fetch_raw_odds_data()  # This already handles multiple sports
                
                if raw_data.get('status') != 'success':
                    error_msg = f"Failed to fetch {sport} data: {raw_data.get('error', 'Unknown error')}"
                    logger.warning(error_msg)
                    failed_sports.append({'sport': sport, 'error': raw_data.get('error')})
                    continue
                
                # Process opportunities for this sport
                sport_opportunities, sport_analytics = process_opportunities(raw_data)
                all_opportunities.extend(sport_opportunities)
                successful_sports.append({
                    'sport': sport, 
                    'opportunities': len(sport_opportunities),
                    'events': raw_data.get('total_events', 0)
                })
                
                logger.info(f"✅ {sport}: {len(sport_opportunities)} opportunities processed")
                
            except Exception as sport_exc:
                logger.error(f"❌ Failed to process {sport}: {str(sport_exc)}")
                failed_sports.append({'sport': sport, 'error': str(sport_exc)})
                # Continue with other sports instead of failing completely
                continue
        
        # Check if we got any data at all
        if not all_opportunities:
            error_msg = f"No opportunities found from any sport. Failed sports: {failed_sports}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"📈 Total opportunities collected: {len(all_opportunities)}")
        
        # Update task state for storage phase
        self.update_state(
            state='PROGRESS',
            meta={
                'current': len(SPORTS_SUPPORTED) + 1,
                'total': len(SPORTS_SUPPORTED) + 2,
                'status': 'Storing processed data...',
                'opportunities_count': len(all_opportunities)
            }
        )
        
        # Generate analytics from all opportunities
        analytics = generate_analytics(all_opportunities)
        
        # Store processed data in Redis with role-based caching
        store_ev_data(all_opportunities)
        store_analytics_data(analytics)
        
        # Store role-specific cached data for performance
        store_role_based_cache(all_opportunities, analytics)
        
        # Publish real-time update
        publish_realtime_update(all_opportunities)
        
        # Final update
        processing_time = time.perf_counter() - start_time
        
        self.update_state(
            state='SUCCESS',
            meta={
                'current': len(SPORTS_SUPPORTED) + 2,
                'total': len(SPORTS_SUPPORTED) + 2,
                'status': 'Complete!'
            }
        )
        
        result = {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_seconds': round(processing_time, 2),
            'opportunities_count': len(all_opportunities),
            'successful_sports': successful_sports,
            'failed_sports': failed_sports,
            'analytics': analytics,
            'performance': {
                'sports_processed': len(successful_sports),
                'sports_failed': len(failed_sports),
                'opportunities_per_second': round(len(all_opportunities) / processing_time, 2)
            }
        }
        
        logger.info(
            f"✅ Odds refresh complete in {processing_time:.2f}s: "
            f"{len(all_opportunities)} opportunities from {len(successful_sports)} sports"
        )
        
        # Log any failures as warnings
        if failed_sports:
            logger.warning(f"⚠️ Some sports failed to process: {failed_sports}")
        
        return result
        
    except Exception as exc:
        processing_time = time.perf_counter() - start_time
        error_details = {
            'error': str(exc),
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_seconds': round(processing_time, 2),
            'retry_count': self.request.retries,
            'max_retries': self.max_retries
        }
        
        logger.error(f"❌ Task failed after {processing_time:.2f}s (retry {self.request.retries}): {str(exc)}")
        
        self.update_state(
            state='FAILURE',
            meta=error_details
        )
        
        # Re-raise for retry logic
        raise exc

def generate_analytics(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate analytics from processed opportunities"""
    if not opportunities:
        return {'total_opportunities': 0, 'avg_ev': 0, 'high_ev_count': 0}
    
    ev_values = [opp.get('EV_Raw', 0) for opp in opportunities if opp.get('EV_Raw')]
    
    return {
        'total_opportunities': len(opportunities),
        'positive_ev_count': len([ev for ev in ev_values if ev > 0]),
        'high_ev_count': len([ev for ev in ev_values if ev >= 0.045]),
        'avg_ev': sum(ev_values) / len(ev_values) if ev_values else 0,
        'max_ev': max(ev_values) if ev_values else 0,
        'last_updated': datetime.utcnow().isoformat()
    }

def store_role_based_cache(opportunities: List[Dict[str, Any]], analytics: Dict[str, Any]):
    """Store pre-filtered data for different user roles to improve performance"""
    try:
        from core.constants import FREE_BET_LIMIT, MASK_FIELDS_FOR_FREE
        
        # Free tier cache (limited and masked)
        free_opportunities = opportunities[:FREE_BET_LIMIT].copy()
        for opp in free_opportunities:
            for field in MASK_FIELDS_FOR_FREE:
                opp.pop(field, None)
        
        # Store in Redis with role-specific keys
        import redis
        import os
        
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        
        # Cache for free users
        redis_client.setex(
            CACHE_KEYS["ev_data_free"], 
            3600,  # 1 hour expiry
            json.dumps(free_opportunities)
        )
        
        # Cache for full access users (subscribers/admins)
        redis_client.setex(
            CACHE_KEYS["ev_data_full"],
            3600,
            json.dumps(opportunities)
        )
        
        logger.info(f"📦 Role-based caches updated: {len(free_opportunities)} free, {len(opportunities)} full")
        
    except Exception as e:
        logger.warning(f"Failed to update role-based cache: {e}")
        # Don't fail the main task for cache issues

def publish_realtime_update(opportunities: List[Dict[str, Any]]):
    """
    Publish real-time update to Redis channel for WebSocket/SSE clients
    """
    try:
        import redis
        import os
        
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        
        # Create update payload for real-time clients
        update_payload = {
            'type': 'ev_update',
            'updated_at': datetime.utcnow().isoformat() + 'Z',  # ISO format with Z suffix
            'data': opportunities[:50],  # Limit payload size for performance
            'summary': {
                'total_count': len(opportunities),
                'positive_ev_count': len([o for o in opportunities if o.get('EV_Raw', 0) > 0]),
                'high_ev_count': len([o for o in opportunities if o.get('EV_Raw', 0) >= 0.045])
            }
        }
        
        # Publish to the real-time updates channel
        redis_client.publish("ev_updates", json.dumps(update_payload))
        logger.info(f"📡 Published real-time update with {len(opportunities)} opportunities at {update_payload['updated_at']}")
        
    except Exception as e:
        logger.warning(f"Failed to publish real-time update: {e}")
        # Don't fail the main task for publishing issues

@shared_task(
    bind=True,
    name="health_check",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    soft_time_limit=30,  # 30 seconds
)
def health_check(self):
    """
    Health check task to verify Celery and Redis connectivity.
    Runs every 5 minutes to ensure the system is operational.
    """
    try:
        logger.info("🔍 Running Celery health check")
        
        # Check Redis connectivity
        redis_status = redis_health_check()
        
        # Basic system checks
        health_result = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'celery_worker': 'operational',
            'redis': redis_status,
            'task_id': self.request.id,
            'retry_count': self.request.retries
        }
        
        if redis_status.get('status') != 'healthy':
            raise Exception(f"Redis health check failed: {redis_status}")
        
        logger.info("✅ Celery health check passed")
        return health_result
        
    except Exception as exc:
        logger.error(f"❌ Health check failed: {str(exc)}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(exc),
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': self.request.retries
            }
        )
        raise exc

@shared_task(
    bind=True,
    name="cleanup_old_data",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2}
)
def cleanup_old_data(self):
    """
    Cleanup task to remove old cached data and results.
    Can be scheduled to run daily to prevent Redis memory issues.
    """
    try:
        logger.info("🧹 Running cleanup task")
        
        import redis
        import os
        
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        
        # Clean up old Celery results (older than 24 hours)
        pattern = "celery-task-meta-*"
        old_keys = []
        
        for key in redis_client.scan_iter(match=pattern):
            try:
                ttl = redis_client.ttl(key)
                if ttl == -1:  # No expiry set
                    redis_client.expire(key, 86400)  # Set 24h expiry
                    old_keys.append(key.decode())
            except Exception:
                continue
        
        result = {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'keys_processed': len(old_keys),
            'action': 'Set expiry on old task results'
        }
        
        logger.info(f"🧹 Cleanup complete: processed {len(old_keys)} keys")
        return result
        
    except Exception as exc:
        logger.error(f"❌ Cleanup task failed: {str(exc)}")
        raise exc

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='process_ev_opportunities'
)
def process_ev_opportunities_task(self):
    """
    Background task to fetch and process betting opportunities.
    Runs periodically to update the dashboard with fresh data.
    """
    global is_shutting_down, active_tasks
    
    # Check if shutting down
    if is_shutting_down:
        logger.info("Task cancelled: system is shutting down")
        return {"status": "cancelled", "reason": "shutdown"}
    
    # Track this task
    task_id = self.request.id
    active_tasks.add(task_id)
    
    try:
        logger.info(f"🚀 Starting EV opportunities processing task {task_id}")
        start_time = time.time()
        
        # Check for shutdown during processing
        if is_shutting_down:
            return {"status": "cancelled", "reason": "shutdown"}
        
        # 1. Fetch raw odds data
        logger.info("📊 Fetching raw odds data...")
        raw_data = fetch_raw_odds_data()
        
        if not raw_data:
            logger.warning("No raw data received from API")
            return {
                "status": "warning",
                "message": "No data available from odds provider",
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            }
        
        # Check for shutdown
        if is_shutting_down:
            return {"status": "cancelled", "reason": "shutdown"}
        
        # 2. Process the raw data into opportunities
        logger.info(f"⚙️  Processing {len(raw_data)} raw events...")
        opportunities = process_opportunities(raw_data)
        
        # Check for shutdown
        if is_shutting_down:
            return {"status": "cancelled", "reason": "shutdown"}
        
        # 3. Cache the processed data
        logger.info("💾 Caching processed opportunities...")
        analytics = generate_analytics(opportunities)
        store_role_based_cache(opportunities, analytics)
        
        # 4. Broadcast updates if not shutting down
        if not is_shutting_down:
            publish_realtime_update(opportunities)
        
        processing_time = time.time() - start_time
        result = {
            "status": "success",
            "total_opportunities": len(opportunities),
            "positive_ev_count": len([o for o in opportunities if o.get('EV_Raw', 0) > 0]),
            "high_ev_count": len([o for o in opportunities if o.get('EV_Raw', 0) >= 0.045]),
            "processing_time": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id
        }
        
        logger.info(f"✅ Task {task_id} completed successfully in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {str(e)}")
        raise self.retry(countdown=60, exc=e)
    finally:
        active_tasks.discard(task_id)

def get_celery_stats():
    """Get Celery worker statistics"""
    try:
        from celery import current_app
        
        # Get active stats
        inspect = current_app.control.inspect()
        
        # Get active tasks
        active = inspect.active()
        active_count = sum(len(tasks) for tasks in active.values()) if active else 0
        
        # Get registered tasks
        registered = inspect.registered()
        registered_count = sum(len(tasks) for tasks in registered.values()) if registered else 0
        
        # Get worker stats
        stats = inspect.stats()
        worker_count = len(stats) if stats else 0
        
        return {
            "worker_count": worker_count,
            "active_tasks": active_count,
            "registered_tasks": registered_count,
            "total_tasks_in_active": len(active_tasks),
            "is_shutting_down": is_shutting_down
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get Celery stats: {str(e)}",
            "worker_count": 0,
            "active_tasks": 0
        } 
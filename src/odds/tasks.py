"""
Odds processing and EV calculation tasks
Domain-specific tasks for odds data fetching, processing, and caching
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from celery import shared_task
from celery.signals import worker_shutdown

from services.celery_app import celery_app
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities
from services.redis_cache import store_ev_data, store_analytics_data
from core.constants import CACHE_KEYS
from config import settings

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

# Global cleanup flags
is_shutting_down = False
active_tasks = set()

@worker_shutdown.connect
def worker_shutdown_handler(_sender=None, **kwargs):
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


@shared_task(
    bind=True,
    name="odds.refresh_odds_data",
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
        
        # Fetch raw data once (it already contains all sports)
        try:
            logger.info("📊 Fetching raw odds data for all sports...")
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 1, 
                    'total': len(SPORTS_SUPPORTED) + 2,
                    'status': 'Fetching odds data for all sports...'
                }
            )
            
            # Fetch raw odds for all sports at once
            raw_data = fetch_raw_odds_data()
            
            if raw_data.get('status') != 'success':
                error_msg = f"Failed to fetch odds data: {raw_data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"✅ Raw data fetched: {raw_data.get('total_events', 0)} events")
            
            # Process opportunities once (it processes all sports)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 2, 
                    'total': len(SPORTS_SUPPORTED) + 2,
                    'status': 'Processing opportunities for all sports...'
                }
            )
            
            logger.info("🔄 Processing opportunities for all sports...")
            sport_opportunities, sport_analytics = process_opportunities(raw_data)
            
            if sport_opportunities:
                all_opportunities.extend(sport_opportunities)
                
                logger.info(f"✅ Processed {len(sport_opportunities)} total opportunities across all sports")
                
                # Add all sports as successful since we processed everything together
                for sport in SPORTS_SUPPORTED:
                    successful_sports.append({
                        'sport': sport, 
                        'opportunities': len(sport_opportunities) // len(SPORTS_SUPPORTED),  # Approximate split
                        'events': raw_data.get('total_events', 0) // len(SPORTS_SUPPORTED)  # Rough estimate
                    })
                    
                logger.info(f"✅ Opportunities distributed across {len(SPORTS_SUPPORTED)} sports")
            
            else:
                error_msg = "No opportunities generated from raw data"
                logger.error(error_msg)
                for sport in SPORTS_SUPPORTED:
                    failed_sports.append({'sport': sport, 'error': 'No opportunities generated'})
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"❌ Failed to process odds data: {str(e)}")
            for sport in SPORTS_SUPPORTED:
                failed_sports.append({'sport': sport, 'error': str(e)})
            raise
        
        # Check if we got any data at all
        if not all_opportunities:
            error_msg = f"No opportunities found from any sport. Failed sports: {failed_sports}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"📈 Total opportunities collected: {len(all_opportunities)}")
        
        # Store role-based cache
        store_role_based_cache(all_opportunities, generate_analytics(all_opportunities))
        
        # Publish real-time updates
        publish_realtime_update(all_opportunities)
        
        # Calculate execution time
        execution_time = time.perf_counter() - start_time
        
        # Final success state
        result = {
            'status': 'success',
            'total_opportunities': len(all_opportunities),
            'successful_sports': successful_sports,
            'failed_sports': failed_sports,
            'execution_time': round(execution_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Task completed successfully in {execution_time:.2f}s")
        logger.info(f"   Total opportunities: {len(all_opportunities)}")
        logger.info(f"   Successful sports: {len(successful_sports)}")
        logger.info(f"   Failed sports: {len(failed_sports)}")
        
        return result
        
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        error_msg = f"Task failed after {execution_time:.2f}s: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Update task state to show failure
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'execution_time': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        raise self.retry(countdown=60, exc=e)


def generate_analytics(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate analytics from opportunities data"""
    if not opportunities:
        return {}
    
    total_opportunities = len(opportunities)
    avg_ev = sum(float(opp.get('ev_percentage', 0)) for opp in opportunities) / total_opportunities if total_opportunities > 0 else 0
    
    return {
        'total_opportunities': total_opportunities,
        'average_ev': round(avg_ev, 2),
        'last_updated': datetime.now().isoformat(),
        'sports_breakdown': _get_sports_breakdown(opportunities)
    }


def _get_sports_breakdown(opportunities: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get breakdown of opportunities by sport"""
    breakdown = {}
    for opp in opportunities:
        sport = opp.get('sport', 'unknown')
        breakdown[sport] = breakdown.get(sport, 0) + 1
    return breakdown


def store_role_based_cache(opportunities: List[Dict[str, Any]], analytics: Dict[str, Any]):
    """Store opportunities and analytics in Redis with role-based segmentation"""
    try:
        # Store for free users (limited data)
        free_opportunities = opportunities[:10]  # Limit to 10 for free users
        store_ev_data(free_opportunities, cache_key=CACHE_KEYS['free_ev_data'])
        
        # Store for paid users (full data)
        store_ev_data(opportunities, cache_key=CACHE_KEYS['paid_ev_data'])
        
        # Store analytics
        store_analytics_data(analytics)
        
        logger.info(f"✅ Cached {len(opportunities)} opportunities (paid) and {len(free_opportunities)} (free)")
        
    except Exception as e:
        logger.error(f"❌ Failed to store role-based cache: {e}")
        raise


def publish_realtime_update(opportunities: List[Dict[str, Any]]):
    """Publish real-time updates to connected clients"""
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        
        # Prepare update payload
        update_payload = {
            'type': 'odds_update',
            'timestamp': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'preview': opportunities[:5] if opportunities else []  # Send preview
        }
        
        # Publish to Redis pub/sub channel
        redis_client.publish('odds_updates', json.dumps(update_payload))
        
        logger.info(f"✅ Published real-time update with {len(opportunities)} opportunities")
        
    except Exception as e:
        logger.error(f"❌ Failed to publish real-time update: {e}")
        # Don't raise - this is non-critical


@shared_task(
    bind=True,
    name="odds.cleanup_old_data",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2}
)
def cleanup_old_data(self):
    """Clean up old cached odds data"""
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        
        # Clean up old cache keys
        old_keys = redis_client.keys("odds:*:old")
        if old_keys:
            redis_client.delete(*old_keys)
            logger.info(f"✅ Cleaned up {len(old_keys)} old cache keys")
        
        return {'status': 'success', 'cleaned_keys': len(old_keys)}
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup old data: {e}")
        raise 
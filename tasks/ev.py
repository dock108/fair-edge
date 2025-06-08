"""
EV Calculation Tasks for bet-intel
Heavy computation moved off the request path per Phase 3.1

This module handles:
- Batch EV calculations using Pandas/NumPy
- Redis caching with TTL
- Progress tracking and error handling
"""

import time
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import shared_task

# Import heavy computation services
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities
from services.redis_cache import redis_client, store_ev_data, store_analytics_data

logger = logging.getLogger(__name__)

# Cache TTL constants
EV_BATCH_TTL = 300  # 5 minutes for batch results
PROCESSING_STATUS_TTL = 600  # 10 minutes for status tracking

@shared_task(
    bind=True,
    name="ev.calc_batch",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=10 * 60,  # 10 minutes soft limit
    time_limit=12 * 60,       # 12 minutes hard limit
)
def calc_ev_batch(self, batch_id: str, _options: Optional[Dict[str, Any]] = None):
    """
    Calculate EV for a batch of opportunities - heavy computation task
    
    Args:
        batch_id: Unique identifier for this batch
        options: Optional parameters for filtering/processing
        
    Returns:
        dict: Results summary with batch info
        
    This task moves CPU-heavy Pandas/NumPy work off the FastAPI event loop
    as recommended in FastAPI + Celery guides
    """
    start_time = time.perf_counter()
    
    try:
        logger.info(f"🧮 Starting EV batch calculation: {batch_id}")
        
        # Update task state to show progress
        self.update_state(
            state='PROGRESS',
            meta={
                'batch_id': batch_id,
                'current': 0,
                'total': 3,
                'status': 'Fetching raw odds data...',
                'start_time': start_time
            }
        )
        
        # Store processing status in Redis
        status_key = f"ev_batch_status:{batch_id}"
        redis_client.setex(
            status_key, 
            PROCESSING_STATUS_TTL,
            json.dumps({
                'status': 'processing',
                'started_at': datetime.utcnow().isoformat(),
                'task_id': self.request.id
            })
        )
        
        # Step 1: Fetch raw data
        logger.info(f"📊 Fetching raw odds data for batch {batch_id}")
        raw_data = fetch_raw_odds_data()
        
        if raw_data.get('status') != 'success':
            error_msg = f"Failed to fetch raw data: {raw_data.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'batch_id': batch_id,
                'current': 1,
                'total': 3,
                'status': 'Processing EV calculations...',
                'events_fetched': raw_data.get('total_events', 0)
            }
        )
        
        # Step 2: Heavy EV computation (this is the CPU-intensive part)
        logger.info(f"🔄 Processing EV opportunities for batch {batch_id}")
        opportunities, analytics = process_opportunities(raw_data)
        
        if not opportunities:
            error_msg = "No opportunities generated from raw data"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'batch_id': batch_id,
                'current': 2,
                'total': 3,
                'status': 'Caching results...',
                'opportunities_generated': len(opportunities)
            }
        )
        
        # Step 3: Store results in Redis with TTL
        batch_cache_key = f"ev_batch_results:{batch_id}"
        results = {
            'batch_id': batch_id,
            'opportunities': opportunities,
            'analytics': analytics,
            'generated_at': datetime.utcnow().isoformat(),
            'processing_time_ms': round((time.perf_counter() - start_time) * 1000, 2),
            'total_opportunities': len(opportunities)
        }
        
        # Cache with TTL
        redis_client.setex(
            batch_cache_key,
            EV_BATCH_TTL,
            json.dumps(results)
        )
        
        # Also update the main cache for immediate access
        store_ev_data(opportunities)
        store_analytics_data(analytics)
        
        # Update final status
        redis_client.setex(
            status_key,
            PROCESSING_STATUS_TTL,
            json.dumps({
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'task_id': self.request.id,
                'results_cache_key': batch_cache_key
            })
        )
        
        processing_time = time.perf_counter() - start_time
        
        logger.info(f"✅ EV batch {batch_id} completed in {processing_time:.2f}s")
        logger.info(f"   Generated {len(opportunities)} opportunities")
        logger.info(f"   Results cached with key: {batch_cache_key}")
        
        return {
            'batch_id': batch_id,
            'status': 'completed',
            'total_opportunities': len(opportunities),
            'processing_time_seconds': round(processing_time, 2),
            'cache_key': batch_cache_key,
            'expires_at': (datetime.utcnow() + timedelta(seconds=EV_BATCH_TTL)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ EV batch {batch_id} failed: {str(e)}")
        
        # Store error status
        error_status_key = f"ev_batch_status:{batch_id}"
        redis_client.setex(
            error_status_key,
            PROCESSING_STATUS_TTL,
            json.dumps({
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat(),
                'task_id': self.request.id
            })
        )
        
        # Re-raise for Celery retry mechanism
        raise

@shared_task(
    bind=True,
    name="ev.calc_incremental",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2}
)
def calc_ev_incremental(self, sport_key: str, market_key: str):
    """
    Calculate EV for a specific sport/market combination - lighter computation
    
    Args:
        sport_key: Sport identifier (e.g., 'americanfootball_nfl')
        market_key: Market type (e.g., 'h2h', 'spreads')
        
    Returns:
        dict: Incremental results for the specific market
    """
    start_time = time.perf_counter()
    
    try:
        logger.info(f"🎯 Starting incremental EV calc: {sport_key} - {market_key}")
        
        # This would implement targeted fetching for specific markets
        # For now, we'll use the same underlying computation but filter results
        raw_data = fetch_raw_odds_data()
        
        if raw_data.get('status') != 'success':
            raise Exception(f"Failed to fetch data for {sport_key}")
        
        opportunities, analytics = process_opportunities(raw_data)
        
        # Filter to specific sport/market if needed
        # This could be enhanced with more granular filtering
        
        processing_time = time.perf_counter() - start_time
        
        logger.info(f"✅ Incremental EV calc completed in {processing_time:.2f}s")
        
        return {
            'sport_key': sport_key,
            'market_key': market_key,
            'opportunities_count': len(opportunities),
            'processing_time_seconds': round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ Incremental EV calc failed for {sport_key}-{market_key}: {str(e)}")
        raise

def get_batch_results(batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve results for a completed batch calculation
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Cached results or None if not found/expired
    """
    try:
        batch_cache_key = f"ev_batch_results:{batch_id}"
        cached_data = redis_client.get(batch_cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        else:
            logger.info(f"No cached results found for batch {batch_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving batch results for {batch_id}: {e}")
        return None

def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current status of a batch calculation
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Status information or None if not found
    """
    try:
        status_key = f"ev_batch_status:{batch_id}"
        status_data = redis_client.get(status_key)
        
        if status_data:
            return json.loads(status_data)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving batch status for {batch_id}: {e}")
        return None

def generate_batch_id() -> str:
    """Generate a unique batch ID for tracking"""
    return f"ev_batch_{int(time.time())}_{uuid.uuid4().hex[:8]}" 
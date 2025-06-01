"""
Celery background tasks for bet-intel
Handles odds data fetching, processing, and caching
"""
from services.celery_app import celery_app
from services.fastapi_data_processor import fetch_raw_odds_data, process_opportunities
from services.redis_cache import store_ev_data, store_analytics_data
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="refresh_odds_data")
def refresh_odds_data(self):
    """
    Background task to refresh odds data and process EV opportunities
    This task fetches fresh data from The Odds API and stores processed results in Redis
    """
    try:
        logger.info("🌀 Celery task started: Refreshing odds data")
        
        # Update task state to show progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 4, 'status': 'Fetching raw odds data...'}
        )
        
        # Fetch raw odds data from The Odds API
        raw_data = fetch_raw_odds_data()
        
        if raw_data.get('status') != 'success':
            error_msg = f"Failed to fetch odds data: {raw_data.get('error', 'Unknown error')}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"Raw data fetched successfully: {raw_data.get('total_events', 0)} events")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 4, 'status': 'Processing opportunities...'}
        )
        
        # Process opportunities from raw data
        ev_data, analytics = process_opportunities(raw_data)
        
        logger.info(f"Processed {len(ev_data)} EV opportunities")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 4, 'status': 'Storing data in Redis...'}
        )
        
        # Store processed data in Redis
        store_ev_data(ev_data)
        store_analytics_data(analytics)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 4, 'status': 'Completing...'}
        )
        
        result = {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'opportunities_count': len(ev_data),
            'total_events': raw_data.get('total_events', 0),
            'analytics': analytics
        }
        
        logger.info(f"✅ Odds data refresh complete: {len(ev_data)} opportunities stored")
        return result
        
    except Exception as exc:
        logger.error(f"❌ Task failed: {str(exc)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'timestamp': datetime.utcnow().isoformat()}
        )
        raise exc

@celery_app.task(name="health_check")
def health_check():
    """Simple health check task to verify Celery is working"""
    logger.info("🔥 Celery health check task executed")
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Celery worker is operational'
    } 
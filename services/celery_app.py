"""
Celery app configuration for bet-intel background tasks
Handles odds data fetching and processing on a schedule with fault tolerance
"""
from celery import Celery
from celery.schedules import crontab
import os
import logging
from core.config import settings

# Configure logging for Celery
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Get refresh interval from environment
REFRESH_INTERVAL_MINUTES = int(os.getenv("REFRESH_INTERVAL_MINUTES", "60"))  # Default 1 hour
REDIS_URL = settings.redis_url

# Create Celery app
celery_app = Celery(
    "bet_intel",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.tasks"]
)

# Production-ready Celery configuration
celery_app.conf.update(
    # Serialization & Content
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone & UTC
    timezone='UTC',
    enable_utc=True,
    
    # Task Tracking & Limits
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker Configuration for Fault Tolerance
    task_acks_late=True,  # Acknowledge after completion for safer crash handling
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker to prevent memory leaks
    worker_disable_rate_limits=False,
    
    # Beat Schedule Configuration - Use exact task names from @shared_task decorators
    beat_schedule={
        'refresh-ev-data': {
            'task': 'refresh_odds_data',  # Matches @shared_task(name="refresh_odds_data")
            'schedule': crontab(minute=f"*/{REFRESH_INTERVAL_MINUTES}"),
            'options': {
                'expires': 60 * REFRESH_INTERVAL_MINUTES,  # Expire if not picked up
                'retry': True,
                'retry_policy': {
                    'max_retries': 3,
                    'interval_start': 0,
                    'interval_step': 30,
                    'interval_max': 300,
                },
                'queue': 'celery',
                'routing_key': 'celery'
            }
        },
        'health-check': {
            'task': 'health_check',  # Matches @shared_task(name="health_check")
            'schedule': crontab(minute='*/5'),
            'options': {
                'expires': 300,
                'queue': 'celery',
                'routing_key': 'celery'
            }
        }
    },
    
    # Result Backend Settings
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
        "retry_policy": {
            "timeout": 5.0
        }
    },
    
    # Task Result Expiration
    result_expires=3600,  # Results expire after 1 hour
    
    # Error Handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)

# Logging configuration for Celery
logger = logging.getLogger('celery')
logger.setLevel(logging.INFO)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Log configuration on startup
logger.info(f"Celery configured with Redis URL: {REDIS_URL}")
logger.info(f"Auto-refresh interval: {REFRESH_INTERVAL_MINUTES} minutes")
logger.info(f"Beat schedule: {list(celery_app.conf.beat_schedule.keys())}")

if __name__ == '__main__':
    celery_app.start() 
"""
Celery app configuration for FairEdge background tasks
Handles odds data fetching and processing on a schedule with fault tolerance
"""
import os
import sys
from celery import Celery
from celery.schedules import crontab
import logging
from core.settings import settings

# Add project root to Python path for imports to work in Celery workers
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure Celery logging before other imports
logging.basicConfig(level=logging.INFO)

# Get configuration from centralized settings
# Aggressive refresh schedule: Every 30 minutes from 7 AM to 10 PM EST
REFRESH_INTERVAL_MINUTES = 30  # Aggressive refresh during business hours
REDIS_URL = settings.redis_url

# Create Celery app with actual task modules
celery_app = Celery(
    "fairedge",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "services.tasks",  # Main tasks module
        "tasks.ev",        # EV calculation tasks
    ]
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
    
    # Beat Scheduler Configuration
    beat_schedule_filename='/app/celery-data/beat.db',  # Store in persistent volume for Docker
    
    # Beat Schedule Configuration - Aggressive refresh during business hours (7 AM to 10 PM EST)
    beat_schedule={
        'business-hours-refresh-ev-data': {
            'task': 'tasks.odds.refresh_data',  # Matches @shared_task(name="tasks.odds.refresh_data")
            'schedule': crontab(
                minute='0,30',  # Every 30 minutes (on the hour and half-hour)
                hour='12-3'     # 7 AM to 10 PM EST = 12 PM to 3 AM UTC (next day)
            ),
            'options': {
                'expires': 60 * REFRESH_INTERVAL_MINUTES,  # Expire if not picked up within 30 minutes
                'retry': True,
                'retry_policy': {
                    'max_retries': 3,
                    'interval_start': 0,
                    'interval_step': 30,
                    'interval_max': 300,
                },
                'queue': 'celery',
                'routing_key': 'celery'
            },
            'kwargs': {
                'force_refresh': False,
                'skip_activity_check': True  # Skip activity checking for scheduled business hours refreshes
            }
        },
        'off-hours-smart-refresh-ev-data': {
            'task': 'tasks.odds.refresh_data',  # Same task, different schedule
            'schedule': crontab(
                minute='0',     # Once per hour (on the hour)
                hour='4-11'     # 11 PM to 6 AM EST = 4 AM to 11 AM UTC
            ),
            'options': {
                'expires': 3600,  # Expire if not picked up within 1 hour
                'retry': True,
                'retry_policy': {
                    'max_retries': 2,  # Fewer retries during off-hours
                    'interval_start': 0,
                    'interval_step': 60,
                    'interval_max': 600,
                },
                'queue': 'celery',
                'routing_key': 'celery'
            },
            'kwargs': {
                'force_refresh': False,
                'skip_activity_check': False  # Use activity checking during off-hours
            }
        },
        'health-check': {
            'task': 'tasks.system.health_check',  # Matches @shared_task(name="tasks.system.health_check")
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
    
    # Result Backend Configuration (fix serialization issues)
    result_accept_content=['json'],
    result_backend_max_retries=3,
    result_backend_retry_on_timeout=True,
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
logger.info(f"Aggressive refresh interval: {REFRESH_INTERVAL_MINUTES} minutes (business hours only)")
logger.info(f"Beat schedule: {list(celery_app.conf.beat_schedule.keys())}")
logger.info("📊 Aggressive refresh strategy: Refreshes every 30 minutes from 7 AM to 10 PM EST, regardless of activity")

if __name__ == '__main__':
    celery_app.start() 
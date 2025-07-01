"""
Celery configuration manager for different environments
Handles local stress testing vs production scheduling
"""
import os
from celery.schedules import crontab

def get_celery_beat_schedule():
    """Get the appropriate Celery beat schedule based on environment"""
    
    environment = os.getenv('ENVIRONMENT', 'development')
    refresh_interval = int(os.getenv('REFRESH_INTERVAL_MINUTES', '15'))
    
    if environment == 'development' or refresh_interval <= 5:
        # Stress test mode for local development
        return {
            'stress-test-refresh-ev-data': {
                'task': 'tasks.odds.refresh_data',
                'schedule': crontab(minute=f"*/{refresh_interval}"),  # Every N minutes
                'options': {
                    'expires': 60 * refresh_interval,
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
                    'skip_activity_check': True  # Always refresh in dev
                }
            },
            'health-check': {
                'task': 'tasks.system.health_check',
                'schedule': crontab(minute='*/5'),
                'options': {
                    'expires': 300,
                    'queue': 'celery',
                    'routing_key': 'celery'
                }
            }
        }
    else:
        # Production mode with business hours scheduling
        return {
            'business-hours-refresh-ev-data': {
                'task': 'tasks.odds.refresh_data',
                'schedule': crontab(
                    minute='0,30',  # Every 30 minutes
                    hour='12-3'     # 7 AM to 10 PM EST = 12 PM to 3 AM UTC
                ),
                'options': {
                    'expires': 60 * 30,
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
                    'skip_activity_check': True  # Skip activity check during business hours
                }
            },
            'off-hours-smart-refresh-ev-data': {
                'task': 'tasks.odds.refresh_data',
                'schedule': crontab(
                    minute='0',     # Once per hour
                    hour='4-11'     # 11 PM to 6 AM EST = 4 AM to 11 AM UTC
                ),
                'options': {
                    'expires': 3600,
                    'retry': True,
                    'retry_policy': {
                        'max_retries': 2,
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
                'task': 'tasks.system.health_check',
                'schedule': crontab(minute='*/5'),
                'options': {
                    'expires': 300,
                    'queue': 'celery',
                    'routing_key': 'celery'
                }
            }
        }

def get_refresh_description():
    """Get a human-readable description of the current refresh strategy"""
    environment = os.getenv('ENVIRONMENT', 'development')
    refresh_interval = int(os.getenv('REFRESH_INTERVAL_MINUTES', '15'))
    
    if environment == 'development' or refresh_interval <= 5:
        return f"🔥 STRESS TEST MODE: Refreshing every {refresh_interval} minutes"
    else:
        return "📊 PRODUCTION MODE: Business hours (7 AM - 10 PM EST) every 30 min, off-hours with activity check"
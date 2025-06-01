"""
Celery app configuration for bet-intel background tasks
Handles odds data fetching and processing on a schedule
"""
from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL_MINUTES", "5"))

celery_app = Celery(
    "bet_intel",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.tasks"]
)

# Basic Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional beat schedule for automatic refresh (can be enabled later)
celery_app.conf.beat_schedule = {
    "refresh-odds-every-N-minutes": {
        "task": "services.tasks.refresh_odds_data",
        "schedule": crontab(minute=f"*/{REFRESH_INTERVAL}"),
        "options": {"expires": 60 * REFRESH_INTERVAL}  # Expire if not picked up in time
    }
}

if __name__ == '__main__':
    celery_app.start() 
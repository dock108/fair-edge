#!/usr/bin/env python3
"""
Celery worker entry point for bet-intel background tasks
Run this script to start the Celery worker that processes background tasks
"""
import os
import sys
from services.celery_app import celery_app

# Explicitly import tasks to ensure they're registered
import services.tasks  # noqa: F401 - Import needed for task registration

def main():
    """Start the Celery worker"""
    print("🚀 Starting bet-intel Celery worker...")
    print(f"Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    
    # Log registered tasks for debugging
    registered_tasks = list(celery_app.tasks.keys())
    print(f"📋 Registered tasks: {registered_tasks}")
    
    # Start the worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=1',
        '--pool=solo'
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Worker shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Worker failed to start: {e}")
        sys.exit(1) 
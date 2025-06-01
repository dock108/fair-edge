#!/usr/bin/env python3
"""
Celery worker entry point for bet-intel background tasks
Run this script to start the Celery worker that processes background tasks
"""
import os
import sys
from services.celery_app import celery_app

def main():
    """Start the Celery worker"""
    print("🚀 Starting bet-intel Celery worker...")
    print(f"Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    
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
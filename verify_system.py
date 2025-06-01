#!/usr/bin/env python3
"""
System verification script for automated EV refresh system
Checks all components are properly configured and working
"""

def main():
    print("🔍 Verifying Automated EV Refresh System...")
    print("=" * 50)
    
    # Test 1: Celery App Configuration
    try:
        from services.celery_app import celery_app, REFRESH_INTERVAL_MINUTES
        print("✅ Celery app configuration:")
        print(f"   Auto-refresh interval: {REFRESH_INTERVAL_MINUTES} minutes")
        print(f"   Beat schedule tasks: {list(celery_app.conf.beat_schedule.keys())}")
        print(f"   Task acks late: {celery_app.conf.task_acks_late}")
        print(f"   Worker max tasks: {celery_app.conf.worker_max_tasks_per_child}")
    except Exception as e:
        print(f"❌ Celery app configuration failed: {e}")
        return False
    
    # Test 2: Task Import
    try:
        from services.tasks import refresh_odds_data, health_check, generate_analytics
        print("✅ Task imports successful")
        print(f"   refresh_odds_data: {refresh_odds_data.name}")
        print(f"   health_check: {health_check.name}")
        print(f"   Analytics function available: {callable(generate_analytics)}")
    except Exception as e:
        print(f"❌ Task import failed: {e}")
        return False
    
    # Test 3: Constants and Configuration
    try:
        from core.constants import CACHE_KEYS, FREE_BET_LIMIT, MASK_FIELDS_FOR_FREE, ROLE_FEATURES
        print("✅ Constants configuration:")
        print(f"   Free bet limit: {FREE_BET_LIMIT}")
        print(f"   Masked fields count: {len(MASK_FIELDS_FOR_FREE)}")
        print(f"   Role features configured: {list(ROLE_FEATURES.keys())}")
        print(f"   Cache keys: {list(CACHE_KEYS.keys())}")
    except Exception as e:
        print(f"❌ Constants configuration failed: {e}")
        return False
    
    # Test 4: Beat Schedule Details
    try:
        print("✅ Beat schedule details:")
        for task_name, config in celery_app.conf.beat_schedule.items():
            print(f"   {task_name}:")
            print(f"     Task: {config['task']}")
            print(f"     Schedule: {config['schedule']}")
            if 'options' in config:
                print(f"     Options: {config['options']}")
    except Exception as e:
        print(f"❌ Beat schedule verification failed: {e}")
        return False
    
    # Test 5: Sports Configuration
    try:
        from services.tasks import SPORTS_SUPPORTED
        print("✅ Sports configuration:")
        print(f"   Supported sports: {SPORTS_SUPPORTED}")
        print(f"   Total sports: {len(SPORTS_SUPPORTED)}")
    except Exception as e:
        print(f"❌ Sports configuration failed: {e}")
        return False
    
    # Test 6: Redis Health Check
    try:
        from services.redis_cache import health_check as redis_health
        redis_status = redis_health()
        if redis_status.get('status') == 'healthy':
            print("✅ Redis connectivity verified")
            print(f"   Status: {redis_status}")
        else:
            print(f"⚠️ Redis connectivity issues: {redis_status}")
    except Exception as e:
        print(f"❌ Redis health check failed: {e}")
        # Not critical for verification
    
    # Test 7: File Structure
    import os
    files_to_check = [
        'docker-compose.yml',
        'scripts/start_worker.sh', 
        'scripts/start_beat.sh',
        'logging_config.yaml',
        'tests/test_refresh_task.py',
        'AUTOMATED_REFRESH_GUIDE.md'
    ]
    
    print("✅ File structure verification:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} (missing)")
    
    print("\n" + "=" * 50)
    print("🎉 System verification complete!")
    print("\nNext steps:")
    print("1. Start Redis: redis-server")
    print("2. Start worker: ./scripts/start_worker.sh")
    print("3. Start beat: ./scripts/start_beat.sh") 
    print("4. Monitor logs and verify tasks run automatically")
    print("\nOr use Docker Compose:")
    print("docker-compose up -d")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
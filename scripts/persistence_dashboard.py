#!/usr/bin/env python3
"""
Fair-Edge Persistence Performance Dashboard

Comprehensive monitoring dashboard for persistence system health and performance.
"""
import sys
import os
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.persistence_monitoring import persistence_monitor, log_performance_metrics
from services.persistence_optimizer import persistence_optimizer
from services.sync_bet_persistence import sync_bet_persistence


def print_header():
    """Print dashboard header"""
    print("\n" + "=" * 70)
    print("🚀 FAIR-EDGE PERSISTENCE PERFORMANCE DASHBOARD")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def print_health_status():
    """Print current health status"""
    print("\n📊 HEALTH STATUS")
    print("-" * 40)
    
    try:
        health = persistence_monitor.check_health()
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        print(f"Overall Status: {status_emoji.get(health['status'], '❓')} {health['status'].upper()}")
        
        # Print checks
        for check_name, check_data in health.get("checks", {}).items():
            status = check_data.get("status", "unknown")
            value = check_data.get("value", "N/A")
            print(f"  {check_name}: {status_emoji.get(status, '❓')} {value}")
        
        # Print warnings and errors
        for warning in health.get("warnings", []):
            print(f"  ⚠️  {warning}")
        for error in health.get("errors", []):
            print(f"  ❌ {error}")
            
    except Exception as e:
        print(f"❌ Failed to get health status: {e}")


def print_performance_summary():
    """Print performance summary"""
    print("\n⚡ PERFORMANCE SUMMARY (24h)")
    print("-" * 40)
    
    try:
        summary = persistence_monitor.get_performance_summary()
        
        print(f"Total Operations: {summary['total_operations']:,}")
        print(f"Total Errors: {summary['total_errors']:,}")
        print(f"Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"System Uptime: {summary['uptime_hours']:.1f} hours")
        
        # Batch operation details
        batch_stats = summary.get("operations_by_type", {}).get("batch_save")
        if batch_stats:
            print(f"\n📦 Batch Operations:")
            print(f"  Count: {batch_stats['count']:,}")
            print(f"  Success Rate: {batch_stats['success_rate']:.1f}%")
            print(f"  Avg Duration: {batch_stats['avg_duration_ms']:.0f}ms")
            print(f"  P95 Duration: {batch_stats['p95_duration_ms']:.0f}ms")
            print(f"  Min Duration: {batch_stats['min_duration_ms']:.0f}ms")
            print(f"  Max Duration: {batch_stats['max_duration_ms']:.0f}ms")
        else:
            print("\n📦 No batch operations recorded")
            
    except Exception as e:
        print(f"❌ Failed to get performance summary: {e}")


def print_optimization_status():
    """Print optimization recommendations"""
    print("\n🔧 OPTIMIZATION STATUS")
    print("-" * 40)
    
    try:
        # Run optimization check
        optimization = persistence_optimizer.optimize_if_needed()
        if optimization:
            print(f"✅ Optimization completed:")
            print(f"  Optimal Batch Size: {optimization['optimal_batch_size']}")
            print(f"  Next Optimization: {optimization['next_optimization']}")
        else:
            print("⏰ No optimization needed at this time")
        
        # Show recommendations
        recommendations = persistence_optimizer.get_performance_recommendations()
        recs = recommendations.get("recommendations", [])
        
        if recs:
            print(f"\n📋 Recommendations ({len(recs)}):")
            for i, rec in enumerate(recs[:5], 1):  # Show top 5
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                print(f"  {i}. {priority_emoji.get(rec['priority'], '⚪')} {rec['message']}")
                print(f"     Action: {rec['action']}")
        else:
            print("\n✅ No performance recommendations at this time")
            
    except Exception as e:
        print(f"❌ Failed to get optimization status: {e}")


def print_recent_errors():
    """Print recent errors"""
    print("\n🚨 RECENT ERRORS")
    print("-" * 40)
    
    try:
        errors = persistence_monitor.get_recent_errors(5)
        if errors:
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error['timestamp']} - {error['operation_type']}")
                if error['details']:
                    print(f"     Details: {str(error['details'])[:60]}...")
        else:
            print("✅ No recent errors")
            
    except Exception as e:
        print(f"❌ Failed to get recent errors: {e}")


def run_test_operation():
    """Run a test persistence operation"""
    print("\n🧪 RUNNING TEST OPERATION")
    print("-" * 40)
    
    try:
        test_opportunity = {
            'Event': f'Dashboard Test {datetime.now().strftime("%H:%M:%S")}',
            'Market': 'h2h',
            'Bet Description': 'Dashboard test operation',
            'Best Available Odds': '+150',
            'Fair Odds': '+120',
            'EV_Raw': 0.025,
            'Best_Odds_Source': 'draftkings',
            'commence_time': datetime.now().isoformat()
        }
        
        start_time = time.time()
        result = sync_bet_persistence.save_opportunities_batch(
            [test_opportunity], 
            source="dashboard_test"
        )
        duration = (time.time() - start_time) * 1000
        
        if result['status'] == 'success':
            print(f"✅ Test completed successfully:")
            print(f"  Duration: {duration:.0f}ms")
            print(f"  Bets Created: {result['bets_created']}")
            print(f"  Offers Created: {result['offers_created']}")
        else:
            print(f"❌ Test failed:")
            print(f"  Errors: {len(result.get('errors', []))}")
            
    except Exception as e:
        print(f"❌ Test operation failed: {e}")


def main():
    """Main dashboard function"""
    try:
        print_header()
        print_health_status()
        print_performance_summary()
        print_optimization_status()
        print_recent_errors()
        
        # Ask if user wants to run test
        print("\n" + "=" * 70)
        run_test = input("Run test persistence operation? (y/N): ").lower().strip()
        if run_test == 'y':
            run_test_operation()
        
        print("\n" + "=" * 70)
        print("📊 Dashboard complete. Use this regularly to monitor persistence health.")
        print("💡 Tip: Set up automated monitoring alerts based on these metrics.")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Dashboard failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
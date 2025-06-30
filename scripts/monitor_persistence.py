#!/usr/bin/env python3
"""
Fair-Edge Data Persistence Monitoring Script

This script checks the status of database persistence and provides insights
into how the data collection is performing.
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from db import get_async_session, check_database_connection
from sqlalchemy import text


async def check_persistence_status():
    """Check the current status of data persistence"""
    print("🔍 Fair-Edge Data Persistence Status Check")
    print("=" * 50)
    
    # Check database connection
    db_connected = await check_database_connection()
    print(f"📡 Database Connection: {'✅ Connected' if db_connected else '❌ Failed'}")
    
    if not db_connected:
        print("❌ Cannot check persistence status - database connection failed")
        return False
    
    try:
        session = await get_async_session()
        try:
            # Check total records
            result = await session.execute(text("SELECT COUNT(*) FROM bets"))
            total_bets = result.scalar()
            print(f"📊 Total Bets: {total_bets:,}")
            
            result = await session.execute(text("SELECT COUNT(*) FROM bet_offers"))
            total_offers = result.scalar()
            print(f"📈 Total Offers: {total_offers:,}")
            
            # Check recent activity (last 24 hours)
            result = await session.execute(text("""
                SELECT COUNT(*) FROM bet_offers 
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """))
            recent_offers = result.scalar()
            print(f"🕐 Recent Offers (24h): {recent_offers:,}")
            
            # Check unique refresh cycles (last 7 days)
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT refresh_cycle_id) FROM bet_offers 
                WHERE timestamp > NOW() - INTERVAL '7 days'
                AND refresh_cycle_id IS NOT NULL
            """))
            refresh_cycles = result.scalar()
            print(f"🔄 Refresh Cycles (7d): {refresh_cycles:,}")
            
            # Check sports distribution
            result = await session.execute(text("""
                SELECT s.name, COUNT(b.bet_id) as bet_count
                FROM sports s
                LEFT JOIN bets b ON s.sport_id = b.sport
                GROUP BY s.sport_id, s.name
                ORDER BY bet_count DESC
            """))
            sports_data = result.fetchall()
            
            print("\n🏈 Sports Distribution:")
            for sport_name, bet_count in sports_data:
                print(f"  {sport_name}: {bet_count:,} bets")
            
            # Check books distribution
            result = await session.execute(text("""
                SELECT bk.name, COUNT(bo.offer_id) as offer_count
                FROM books bk
                LEFT JOIN bet_offers bo ON bk.book_id = bo.book
                GROUP BY bk.book_id, bk.name
                ORDER BY offer_count DESC
                LIMIT 10
            """))
            books_data = result.fetchall()
            
            print("\n📚 Top Books by Offers:")
            for book_name, offer_count in books_data:
                if offer_count > 0:
                    print(f"  {book_name}: {offer_count:,} offers")
            
            # Check data quality
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(event_time) as with_event_time,
                    COUNT(sha_key) as with_sha_key
                FROM bets
            """))
            quality_data = result.fetchone()
            
            print(f"\n✅ Data Quality:")
            print(f"  Event Time Coverage: {quality_data.with_event_time}/{quality_data.total} ({quality_data.with_event_time/quality_data.total*100:.1f}%)")
            print(f"  SHA Key Coverage: {quality_data.with_sha_key}/{quality_data.total} ({quality_data.with_sha_key/quality_data.total*100:.1f}%)")
            
            # Estimate persistence health
            if recent_offers > 0:
                print(f"\n🎉 Persistence Status: ✅ ACTIVE")
                print(f"   Data is being collected successfully")
            else:
                print(f"\n⚠️  Persistence Status: ❓ NO RECENT ACTIVITY")
                print(f"   No offers recorded in the last 24 hours")
            
            return True
        finally:
            await session.close()
            
    except Exception as e:
        print(f"❌ Error checking persistence status: {e}")
        return False


async def test_persistence_service():
    """Test the persistence service with sample data"""
    print("\n🧪 Testing Persistence Service")
    print("-" * 30)
    
    try:
        from services.sync_bet_persistence import sync_bet_persistence
        
        # Create test opportunity
        test_opportunity = {
            'Event': f'Test Event {datetime.now().strftime("%H:%M:%S")}',
            'Market': 'h2h',
            'Bet Description': 'Test bet for monitoring',
            'Best Available Odds': '+150',
            'Fair Odds': '+120',
            'EV_Raw': 0.025,
            'Best_Odds_Source': 'test_source',
            'commence_time': datetime.now().isoformat()
        }
        
        print("📝 Running test persistence...")
        result = sync_bet_persistence.save_opportunities_batch(
            [test_opportunity], 
            source="monitoring_test"
        )
        
        print(f"✅ Test completed:")
        print(f"   Status: {result['status']}")
        print(f"   Processing time: {result['processing_time_ms']}ms")
        
        if result.get('errors'):
            print(f"⚠️  Errors: {len(result['errors'])}")
            for error in result['errors'][:2]:
                print(f"     {error.get('type', 'unknown')}: {error.get('message', 'no message')[:80]}...")
        else:
            print(f"   No errors - persistence working correctly!")
        
        return result['status'] == 'success'
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """Main monitoring function"""
    try:
        # Check persistence status
        status_ok = await check_persistence_status()
        
        if status_ok:
            # Test persistence service
            test_ok = await test_persistence_service()
            
            print("\n" + "=" * 50)
            if test_ok:
                print("🎉 Persistence system is working correctly!")
                print("✅ Data collection is active and functional")
            else:
                print("⚠️  Persistence system has issues")
                print("❗ Check logs and database configuration")
        
        return status_ok
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
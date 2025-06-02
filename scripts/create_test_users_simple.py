#!/usr/bin/env python3
"""
Simple script to create test user profiles
Usage: python scripts/create_test_users_simple.py
"""

import sys
import asyncio
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_users():
    """Create test users with fixed UUIDs"""
    
    test_users = [
        {
            'id': '11111111-1111-1111-1111-111111111111',
            'email': 'free-user@test.com',
            'role': 'free',
            'subscription_status': 'none'
        },
        {
            'id': '22222222-2222-2222-2222-222222222222',
            'email': 'paid-user@test.com',
            'role': 'subscriber',
            'subscription_status': 'active'
        },
        {
            'id': '33333333-3333-3333-3333-333333333333',
            'email': 'admin-user@test.com',
            'role': 'admin',
            'subscription_status': 'active'
        }
    ]
    
    async with engine.begin() as conn:
        logger.info("Creating test users...")
        
        for user in test_users:
            try:
                # Check if user exists
                check_result = await conn.execute(
                    text("SELECT id FROM profiles WHERE email = :email"),
                    {'email': user['email']}
                )
                existing = check_result.fetchone()
                
                if existing:
                    # Update existing user
                    await conn.execute(
                        text("""
                            UPDATE profiles 
                            SET role = :role, subscription_status = :subscription_status
                            WHERE email = :email
                        """),
                        user
                    )
                    logger.info(f"✅ Updated {user['role']} user: {user['email']}")
                else:
                    # Insert new user with fixed UUID
                    await conn.execute(
                        text("""
                            INSERT INTO profiles (id, email, role, subscription_status, created_at)
                            VALUES (:id, :email, :role, :subscription_status, NOW())
                        """),
                        user
                    )
                    logger.info(f"✅ Created {user['role']} user: {user['email']} (ID: {user['id']})")
                
            except Exception as e:
                logger.error(f"❌ Failed to create user {user['email']}: {e}")
                # Continue with other users instead of failing completely
                continue
        
        # Verify the users
        logger.info("\nVerifying test users...")
        result = await conn.execute(
            text("""
                SELECT id, email, role, subscription_status
                FROM profiles 
                WHERE email IN ('free-user@test.com', 'paid-user@test.com', 'admin-user@test.com')
                ORDER BY role
            """)
        )
        
        users = result.fetchall()
        
        if users:
            logger.info("\n📋 Test Users:")
            logger.info("-" * 80)
            for user in users:
                user_id, email, role, sub_status = user
                logger.info(f"ID: {user_id}")
                logger.info(f"Email: {email}")
                logger.info(f"Role: {role}")
                logger.info(f"Subscription: {sub_status}")
                logger.info("-" * 80)
        
        return len(users)

async def main():
    try:
        count = await create_test_users()
        if count > 0:
            print(f"\n🎉 {count} test users ready!")
            print("\nTest accounts:")
            print("• Free User: free-user@test.com (ID: 11111111-1111-1111-1111-111111111111)")
            print("• Paid User: paid-user@test.com (ID: 22222222-2222-2222-2222-222222222222)")
            print("• Admin User: admin-user@test.com (ID: 33333333-3333-3333-3333-333333333333)")
        else:
            print("❌ No test users created")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
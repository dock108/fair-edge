#!/usr/bin/env python3
"""
Script to create test users for each role level
Usage: python scripts/create_test_users.py
"""

import sys
import asyncio
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules after path setup
from sqlalchemy import text
from db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_users():
    """Create test users for each role level"""
    
    test_users = [
        {
            'email': 'free-user@test.com',
            'role': 'free',
            'subscription_status': 'none',
            'description': 'Free tier user with limited access'
        },
        {
            'email': 'paid-user@test.com', 
            'role': 'subscriber',
            'subscription_status': 'active',
            'description': 'Premium subscriber with full access'
        },
        {
            'email': 'admin-user@test.com',
            'role': 'admin', 
            'subscription_status': 'active',
            'description': 'Administrator with all privileges'
        }
    ]
    
    async with engine.begin() as conn:
        logger.info("Creating test users...")
        
        for user in test_users:
            try:
                # Check if user already exists
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
                        {
                            'email': user['email'],
                            'role': user['role'],
                            'subscription_status': user['subscription_status']
                        }
                    )
                    logger.info(f"✅ Updated {user['role']} user: {user['email']}")
                else:
                    # Insert new user
                    await conn.execute(
                        text("""
                            INSERT INTO profiles (id, email, role, subscription_status, created_at)
                            VALUES (gen_random_uuid(), :email, :role, :subscription_status, NOW())
                        """),
                        {
                            'email': user['email'],
                            'role': user['role'],
                            'subscription_status': user['subscription_status']
                        }
                    )
                    logger.info(f"✅ Created {user['role']} user: {user['email']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create user {user['email']}: {e}")
                raise
        
        # Verify the users were created
        logger.info("\nVerifying test users...")
        result = await conn.execute(
            text("""
                SELECT email, role, subscription_status, created_at
                FROM profiles 
                WHERE email IN ('free-user@test.com', 'paid-user@test.com', 'admin-user@test.com')
                ORDER BY 
                    CASE role 
                        WHEN 'free' THEN 1 
                        WHEN 'subscriber' THEN 2 
                        WHEN 'admin' THEN 3 
                    END
            """)
        )
        
        users = result.fetchall()
        
        if users:
            logger.info("\n📋 Test Users Created:")
            logger.info("-" * 60)
            for user in users:
                email, role, sub_status, created = user
                logger.info(f"Email: {email}")
                logger.info(f"Role: {role}")
                logger.info(f"Subscription: {sub_status}")
                logger.info(f"Created: {created}")
                logger.info("-" * 60)
        else:
            logger.warning("❌ No test users found after creation")
            return False
    
    logger.info("✅ All test users created successfully!")
    return True

async def main():
    try:
        success = await create_test_users()
        if success:
            print("\n🎉 Test users created successfully!")
            print("\nYou can now test with these accounts:")
            print("• Free User: free-user@test.com")
            print("• Paid User: paid-user@test.com")  
            print("• Admin User: admin-user@test.com")
            print("\nNote: You'll need to handle authentication separately")
        else:
            print("❌ Failed to create test users")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error creating test users: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
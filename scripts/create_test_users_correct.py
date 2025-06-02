#!/usr/bin/env python3
"""
Script to create test users in the correct sequence:
1. Create auth.users records in Supabase
2. Create corresponding profiles records
Usage: python scripts/create_test_users_correct.py
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
    """Create test users in auth.users first, then profiles"""
    
    test_users = [
        {
            'id': '11111111-1111-1111-1111-111111111111',
            'email': 'free-user@test.com',
            'role': 'free',
            'subscription_status': 'none',
            'password': 'testpassword123'
        },
        {
            'id': '22222222-2222-2222-2222-222222222222',
            'email': 'paid-user@test.com',
            'role': 'subscriber',
            'subscription_status': 'active',
            'password': 'testpassword123'
        },
        {
            'id': '33333333-3333-3333-3333-333333333333',
            'email': 'admin-user@test.com',
            'role': 'admin',
            'subscription_status': 'active',
            'password': 'testpassword123'
        }
    ]
    
    # Step 1: Create auth users using Supabase
    logger.info("Step 1: Creating auth users in Supabase...")
    
    async with engine.begin() as conn:
        for user in test_users:
            try:
                # Check if auth user already exists
                auth_check = await conn.execute(
                    text("SELECT id FROM auth.users WHERE email = :email"),
                    {'email': user['email']}
                )
                existing_auth = auth_check.fetchone()
                
                if not existing_auth:
                    # Create auth user directly in database
                    await conn.execute(
                        text("""
                            INSERT INTO auth.users (
                                id, email, encrypted_password, email_confirmed_at, 
                                created_at, updated_at, role, aud, confirmation_token
                            ) VALUES (
                                :id, :email, crypt(:password, gen_salt('bf')), NOW(), 
                                NOW(), NOW(), 'authenticated', 'authenticated', ''
                            )
                        """),
                        {
                            'id': user['id'],
                            'email': user['email'],
                            'password': user['password']
                        }
                    )
                    logger.info(f"✅ Created auth user: {user['email']}")
                else:
                    logger.info(f"ℹ️  Auth user already exists: {user['email']}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to create auth user {user['email']}: {e}")
                continue
    
    # Step 2: Create profile records
    logger.info("\nStep 2: Creating profile records...")
    
    async with engine.begin() as conn:
        for user in test_users:
            try:
                # Check if profile already exists
                profile_check = await conn.execute(
                    text("SELECT id FROM profiles WHERE email = :email"),
                    {'email': user['email']}
                )
                existing_profile = profile_check.fetchone()
                
                if existing_profile:
                    # Update existing profile
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
                    logger.info(f"✅ Updated profile: {user['email']}")
                else:
                    # Create new profile
                    await conn.execute(
                        text("""
                            INSERT INTO profiles (id, email, role, subscription_status, created_at)
                            VALUES (:id, :email, :role, :subscription_status, NOW())
                        """),
                        {
                            'id': user['id'],
                            'email': user['email'],
                            'role': user['role'],
                            'subscription_status': user['subscription_status']
                        }
                    )
                    logger.info(f"✅ Created profile: {user['email']}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to create profile {user['email']}: {e}")
                continue
    
    # Step 3: Verify the users
    logger.info("\nStep 3: Verifying created users...")
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT p.id, p.email, p.role, p.subscription_status, u.created_at
                FROM profiles p
                JOIN auth.users u ON p.id = u.id
                WHERE p.email IN ('free-user@test.com', 'paid-user@test.com', 'admin-user@test.com')
                ORDER BY p.role
            """)
        )
        
        users = result.fetchall()
        
        if users:
            logger.info("\n📋 Test Users Created Successfully:")
            logger.info("-" * 80)
            for user in users:
                user_id, email, role, sub_status, created = user
                logger.info(f"ID: {user_id}")
                logger.info(f"Email: {email}")
                logger.info(f"Role: {role}")
                logger.info(f"Subscription: {sub_status}")
                logger.info(f"Created: {created}")
                logger.info("-" * 80)
        
        return len(users)

async def main():
    try:
        count = await create_test_users()
        if count > 0:
            print(f"\n🎉 {count} test users created successfully!")
            print("\nTest accounts (password: testpassword123):")
            print("• Free User: free-user@test.com")
            print("• Paid User: paid-user@test.com")
            print("• Admin User: admin-user@test.com")
            print("\nThese users can now login with their email and password!")
        else:
            print("❌ No test users created")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
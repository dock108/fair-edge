#!/usr/bin/env python3
"""
Script to create pre-confirmed test users in Supabase
This bypasses email verification issues during testing
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test users to create
TEST_USERS = [
    {
        'email': 'test-free@fairedge.com',
        'password': 'TestPassword123!',
        'role': 'free',
        'subscription_status': 'none',
        'first_name': 'Test',
        'last_name': 'Free'
    },
    {
        'email': 'test-basic@fairedge.com', 
        'password': 'TestPassword123!',
        'role': 'subscriber',
        'subscription_status': 'active',
        'first_name': 'Test',
        'last_name': 'Basic'
    },
    {
        'email': 'test-premium@fairedge.com',
        'password': 'TestPassword123!',
        'role': 'subscriber',
        'subscription_status': 'active',
        'first_name': 'Test',
        'last_name': 'Premium'
    }
]

async def create_test_users():
    """Create test users in Supabase with pre-confirmed email"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        logger.error("Missing Supabase credentials. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    # Create admin client
    supabase: Client = create_client(url, service_key)
    
    logger.info("Creating test users in Supabase...")
    
    for user_data in TEST_USERS:
        try:
            # Create user with admin client (bypasses email verification)
            auth_response = supabase.auth.admin.create_user({
                'email': user_data['email'],
                'password': user_data['password'],
                'email_confirm': True,  # Skip email verification
                'user_metadata': {
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name']
                }
            })
            
            if auth_response.user:
                user_id = auth_response.user.id
                logger.info(f"✅ Created Supabase user: {user_data['email']} (ID: {user_id})")
                
                # Create/update profile in backend database
                profile_data = {
                    'id': user_id,
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'subscription_status': user_data['subscription_status']
                }
                
                # Upsert profile
                profile_response = supabase.table('profiles').upsert(profile_data).execute()
                
                if profile_response.data:
                    logger.info(f"✅ Created/updated profile for: {user_data['email']}")
                else:
                    logger.warning(f"⚠️ Failed to create profile for: {user_data['email']}")
                    
            else:
                logger.error(f"❌ Failed to create Supabase user: {user_data['email']}")
                
        except Exception as e:
            logger.error(f"❌ Error creating user {user_data['email']}: {str(e)}")
            continue
    
    # Verify users were created
    logger.info("\n📋 Verifying test users...")
    try:
        profiles = supabase.table('profiles').select('*').in_('email', [u['email'] for u in TEST_USERS]).execute()
        
        if profiles.data:
            logger.info(f"✅ Found {len(profiles.data)} test users in database")
            for profile in profiles.data:
                logger.info(f"   - {profile['email']}: {profile['role']} ({profile['subscription_status']})")
        else:
            logger.warning("❌ No test users found in database")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying users: {str(e)}")
        return False
    
    return True

async def main():
    try:
        success = await create_test_users()
        if success:
            print("\n🎉 Test users created successfully!")
            print("\nYou can now use these accounts for testing:")
            for user in TEST_USERS:
                print(f"• {user['role'].title()} User: {user['email']}")
            print("\nThese users have confirmed emails and can login immediately.")
        else:
            print("❌ Failed to create test users")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
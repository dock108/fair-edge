#!/usr/bin/env python3
"""
Script to update test user roles to their proper values
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_test_user_roles():
    """Update test user roles to their proper values"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL', 'PLACEHOLDER_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'PLACEHOLDER_KEY')
    
    # Create admin client
    supabase: Client = create_client(url, service_key)
    
    # Update the roles for test users
    role_updates = [
        ('test-free@fairedge.com', 'free', 'none'),
        ('test-basic@fairedge.com', 'basic', 'active'),  # Changed to basic
        ('test-premium@fairedge.com', 'subscriber', 'active')  # Keep as subscriber (premium)
    ]
    
    logger.info("Updating test user roles...")
    
    for email, role, status in role_updates:
        try:
            result = supabase.table('profiles').update({
                'role': role,
                'subscription_status': status
            }).eq('email', email).execute()
            
            if result.data:
                logger.info(f"✅ Updated {email}: {role} ({status})")
            else:
                logger.warning(f"⚠️ No rows updated for {email}")
                
        except Exception as e:
            logger.error(f"❌ Error updating {email}: {str(e)}")
    
    # Verify the updates
    logger.info("\n📋 Verifying updated roles...")
    try:
        profiles = supabase.table('profiles').select('*').in_('email', [u[0] for u in role_updates]).execute()
        
        if profiles.data:
            logger.info(f"✅ Updated {len(profiles.data)} test users")
            for profile in profiles.data:
                logger.info(f"   - {profile['email']}: {profile['role']} ({profile['subscription_status']})")
        else:
            logger.warning("❌ No test users found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying updates: {str(e)}")
        return False
    
    return True

async def main():
    try:
        success = await update_test_user_roles()
        if success:
            print("\n🎉 Test user roles updated successfully!")
            print("\nTest users are now configured with proper roles:")
            print("• Free User: test-free@fairedge.com / TestPassword123!")
            print("• Basic User: test-basic@fairedge.com / TestPassword123!")
            print("• Premium User: test-premium@fairedge.com / TestPassword123!")
        else:
            print("❌ Failed to update test user roles")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
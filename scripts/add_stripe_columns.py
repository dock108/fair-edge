"""
Database migration script to add Stripe-related columns to profiles table
Run this script to add stripe_customer_id and stripe_subscription_id columns
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_stripe_columns():
    """
    Add Stripe-related columns to the profiles table
    """
    # Load environment variables
    load_dotenv()
    
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    if not db_connection_string:
        logger.error("DB_CONNECTION_STRING not found in environment variables")
        return False
    
    try:
        # Create async engine
        engine = create_async_engine(db_connection_string)
        
        async with engine.begin() as conn:
            # Check if columns already exist
            check_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'profiles' 
                AND column_name IN ('stripe_customer_id', 'stripe_subscription_id')
            """
            
            result = await conn.execute(text(check_columns_query))
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'stripe_customer_id' in existing_columns and 'stripe_subscription_id' in existing_columns:
                logger.info("✅ Stripe columns already exist in profiles table")
                return True
            
            # Add missing columns
            if 'stripe_customer_id' not in existing_columns:
                logger.info("Adding stripe_customer_id column...")
                await conn.execute(text("""
                    ALTER TABLE profiles 
                    ADD COLUMN stripe_customer_id TEXT
                """))
                logger.info("✅ Added stripe_customer_id column")
            
            if 'stripe_subscription_id' not in existing_columns:
                logger.info("Adding stripe_subscription_id column...")
                await conn.execute(text("""
                    ALTER TABLE profiles 
                    ADD COLUMN stripe_subscription_id TEXT
                """))
                logger.info("✅ Added stripe_subscription_id column")
            
            # Create index on stripe_subscription_id for faster lookups
            logger.info("Creating index on stripe_subscription_id...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_profiles_stripe_subscription_id 
                ON profiles(stripe_subscription_id)
            """))
            logger.info("✅ Created index on stripe_subscription_id")
            
            # Create index on stripe_customer_id for faster lookups
            logger.info("Creating index on stripe_customer_id...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer_id 
                ON profiles(stripe_customer_id)
            """))
            logger.info("✅ Created index on stripe_customer_id")
        
        await engine.dispose()
        logger.info("🎉 Successfully added Stripe columns to profiles table")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding Stripe columns: {e}")
        return False


async def verify_migration():
    """
    Verify that the migration was successful
    """
    # Load environment variables
    load_dotenv()
    
    db_connection_string = os.getenv('DB_CONNECTION_STRING')
    if not db_connection_string:
        logger.error("DB_CONNECTION_STRING not found in environment variables")
        return False
    
    try:
        engine = create_async_engine(db_connection_string)
        
        async with engine.begin() as conn:
            # Check table structure
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'profiles' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            logger.info("📋 Current profiles table structure:")
            for column in columns:
                logger.info(f"  - {column[0]} ({column[1]}) {'NULL' if column[2] == 'YES' else 'NOT NULL'}")
            
            # Verify Stripe columns exist
            stripe_columns = [col[0] for col in columns if col[0].startswith('stripe_')]
            if 'stripe_customer_id' in stripe_columns and 'stripe_subscription_id' in stripe_columns:
                logger.info("✅ Stripe columns verified successfully")
                return True
            else:
                logger.error("❌ Stripe columns not found")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False


async def main():
    """
    Main migration function
    """
    print("🚀 Starting Stripe columns migration")
    print("=" * 50)
    
    # Add Stripe columns
    success = await add_stripe_columns()
    if not success:
        print("❌ Migration failed")
        return
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    verified = await verify_migration()
    if not verified:
        print("❌ Migration verification failed")
        return
    
    print("=" * 50)
    print("✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with Stripe credentials")
    print("2. Test the billing endpoints")
    print("3. Set up Stripe webhooks")


if __name__ == "__main__":
    asyncio.run(main()) 
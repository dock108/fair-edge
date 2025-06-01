"""
Database setup script for creating additional tables in Supabase
Run this after setting up the profiles table and trigger in Supabase
"""
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_environment():
    """
    Load environment variables from .env file
    """
    # Try to find .env file in current directory or parent directories
    env_path = Path('.env')
    if not env_path.exists():
        # Try parent directory
        env_path = Path('../.env')
        if not env_path.exists():
            # Try looking in the script's directory
            script_dir = Path(__file__).parent
            env_path = script_dir / '.env'

    print(f"🔍 Looking for .env file at: {env_path.absolute()}")
    if env_path.exists():
        # Force reload by clearing existing environment variables first
        supabase_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'DB_CONNECTION_STRING']
        for var in supabase_vars:
            if var in os.environ:
                print(f"   🔄 Clearing cached {var}")
                del os.environ[var]
        
        load_dotenv(env_path, override=True)  # Force override existing values
        print(f"✅ Loaded .env file from: {env_path.absolute()}")
        return True
    else:
        print("⚠️  .env file not found, using system environment variables")
        return False


def check_environment_variables():
    """
    Check if required environment variables are set
    """
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY',
        'DB_CONNECTION_STRING'
    ]
    
    missing_vars = []
    print("\n🔧 Environment Variable Check:")
    print("-" * 40)
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show partial value for security
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"✅ {var}: {display_value}")
            
            # Special validation for DB_CONNECTION_STRING
            if var == 'DB_CONNECTION_STRING':
                print(f"   🔍 Full connection string start: {value[:50]}...")
                if not value.startswith('postgresql+asyncpg://'):
                    print(f"   ❌ ERROR: Must start with 'postgresql+asyncpg://' not '{value.split('://')[0]}://'")
                    print(f"   💡 Current value starts with: {value[:30]}")
                    return False
                else:
                    print("   ✅ Correct async driver detected")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all Supabase credentials are set.")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def create_tables():
    """
    Create all tables defined in models.py
    Note: The profiles table should already exist in Supabase with the trigger
    """
    try:
        # Import here to ensure environment is loaded first
        from db import engine
        from models import Base
        
        if not engine:
            logger.error("Database engine not configured. Check your environment variables.")
            return False
        
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            # Create all tables (will skip if they already exist)
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


async def verify_setup():
    """
    Verify that the database setup is working correctly
    """
    try:
        # Import here to ensure environment is loaded first
        from db import get_database_status
        
        logger.info("Verifying database setup...")
        
        # Check database connection
        status = await get_database_status()
        logger.info(f"Database status: {status}")
        
        if status["overall_status"] == "healthy":
            logger.info("✅ Database setup verification successful")
            return True
        else:
            logger.error("❌ Database setup verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False


async def main():
    """
    Main setup function
    """
    print("🚀 Starting Bet-Intel Database Setup")
    print("=" * 50)
    
    # Load environment variables first
    load_environment()
    
    # Check environment variables
    if not check_environment_variables():
        print("\n❌ Environment setup failed. Cannot proceed without proper configuration.")
        print("\nPlease:")
        print("1. Ensure your .env file exists in the project root")
        print("2. Add all required Supabase credentials to .env")
        print("3. Run this script again")
        return
    
    # Create tables
    print("\n📊 Creating database tables...")
    tables_created = await create_tables()
    if not tables_created:
        print("❌ Failed to create tables. Check your Supabase connection.")
        return
    
    # Verify setup
    print("\n🔍 Verifying database setup...")
    verification_passed = await verify_setup()
    if not verification_passed:
        print("❌ Setup verification failed.")
        return
    
    print("=" * 50)
    print("✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your FastAPI application: python app.py")
    print("2. Test the debug endpoints:")
    print("   - http://localhost:8000/debug/database-status")
    print("   - http://localhost:8000/debug/profiles")
    print("   - http://localhost:8000/debug/supabase")
    print("3. Check the enhanced /health endpoint")


if __name__ == "__main__":
    asyncio.run(main()) 
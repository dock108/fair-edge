"""
Database connection module for Supabase integration
Provides both SQLAlchemy async engine and Supabase client for different use cases
"""
import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# Validate required environment variables
if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DB_CONNECTION_STRING]):
    logger.warning("Missing Supabase environment variables. Database features will be limited.")

# SQLAlchemy async engine setup
engine = None
AsyncSessionLocal = None
Base = declarative_base()

if DB_CONNECTION_STRING:
    try:
        # Validate that we're using the async driver
        if not DB_CONNECTION_STRING.startswith('postgresql+asyncpg://'):
            logger.error("Database connection string must use 'postgresql+asyncpg://' for async support.")
            logger.error(f"Current: {DB_CONNECTION_STRING[:30]}...")
            logger.error("Please update your DB_CONNECTION_STRING to use: postgresql+asyncpg://...")
            raise ValueError("Invalid database driver: async driver required")
        
        engine = create_async_engine(
            DB_CONNECTION_STRING, 
            echo=False,  # Set to True for SQL debugging
            future=True,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=300,    # Recycle connections every 5 minutes
        )
        AsyncSessionLocal = async_sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        logger.info("SQLAlchemy async engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
        if "psycopg2" in str(e):
            logger.error("TIP: Make sure your DB_CONNECTION_STRING uses 'postgresql+asyncpg://' not 'postgresql://'")
        engine = None
        AsyncSessionLocal = None

# Supabase client setup (for auth and convenience methods)
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")

# Supabase client for frontend (anon key)
supabase_anon: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase anonymous client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase anonymous client: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database sessions
    Usage: db: AsyncSession = Depends(get_db)
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Database not properly configured. Check DB_CONNECTION_STRING environment variable.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


def get_supabase() -> Client:
    """
    Get Supabase client for server-side operations
    """
    if not supabase:
        raise RuntimeError("Supabase client not properly configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    return supabase


def get_supabase_anon() -> Client:
    """
    Get Supabase anonymous client for frontend operations
    """
    if not supabase_anon:
        raise RuntimeError("Supabase anonymous client not properly configured. Check SUPABASE_URL and SUPABASE_ANON_KEY.")
    return supabase_anon


async def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    if not engine:
        return False
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def check_supabase_connection() -> bool:
    """
    Check if Supabase client connection is working
    """
    if not supabase:
        return False
    
    try:
        # Try to query profiles table (non-sensitive check)
        response = supabase.table('profiles').select('id').limit(1).execute()
        return response.data is not None
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        return False


# Health check function for API
async def get_database_status() -> dict:
    """
    Get comprehensive database status for health checks
    """
    sqlalchemy_connected = await check_database_connection()
    supabase_connected = await check_supabase_connection()
    
    return {
        "sqlalchemy_engine": {
            "configured": engine is not None,
            "connected": sqlalchemy_connected
        },
        "supabase_client": {
            "configured": supabase is not None,
            "connected": supabase_connected
        },
        "overall_status": "healthy" if (sqlalchemy_connected and supabase_connected) else "degraded"
    } 
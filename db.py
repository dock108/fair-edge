"""
Supabase REST API Database Module

This module provides Supabase client connections for the Fair-Edge application.
All database operations use Supabase REST API - no direct PostgreSQL
connections.

Key Functions:
- get_supabase(): Get Supabase service client for server-side operations
- get_supabase_anon(): Get Supabase anonymous client for frontend operations
- check_supabase_connection(): Test Supabase connectivity
- get_database_status(): Health check information

Legacy functions are kept for compatibility but raise errors directing to
Supabase usage.
"""
import logging
import os

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate required environment variables
if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY]):
    logger.warning("Missing Supabase environment variables. " "Database features will be limited.")

# Supabase client setup (for server-side operations)
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase service client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase service client: {e}")

# Supabase client for frontend (anon key)
supabase_anon: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase anonymous client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase anonymous client: {e}")


def get_supabase() -> Client:
    """
    Get Supabase client for server-side operations
    """
    if not supabase:
        raise RuntimeError(
            "Supabase client not properly configured. "
            "Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return supabase


def get_supabase_anon() -> Client:
    """
    Get Supabase anonymous client for frontend operations
    """
    if not supabase_anon:
        raise RuntimeError(
            "Supabase anonymous client not properly configured. "
            "Check SUPABASE_URL and SUPABASE_ANON_KEY."
        )
    return supabase_anon


async def check_supabase_connection() -> bool:
    """
    Check if Supabase client connection is working
    """
    if not supabase:
        return False

    try:
        # Try to query profiles table (non-sensitive check)
        response = supabase.table("profiles").select("id").limit(1).execute()
        return response.data is not None
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        return False


async def get_database_status() -> dict:
    """
    Get database status for health checks (Supabase REST API only)
    """
    supabase_connected = await check_supabase_connection()

    return {
        "supabase_client": {"configured": supabase is not None, "connected": supabase_connected},
        "overall_status": "healthy" if supabase_connected else "degraded",
        "persistence_method": "supabase_rest_api",
    }


# Legacy compatibility function - no longer needed
async def get_db():
    """
    Legacy function for FastAPI dependency injection compatibility.
    This function is no longer used since we refactored to Supabase REST API.
    Kept for any remaining legacy code that might reference it.
    """
    raise RuntimeError("get_db() is deprecated. Use get_supabase() directly instead.")


async def get_async_session():
    """
    Legacy compatibility stub - no longer used.
    All database operations now use Supabase REST API directly.
    """
    raise RuntimeError("Direct PostgreSQL sessions disabled. Use get_supabase() instead.")


async def execute_with_pgbouncer_retry(session, params: dict = None, max_retries: int = 2):
    """
    Legacy compatibility stub - no longer used.
    All database operations now use Supabase REST API directly.
    """
    raise RuntimeError("Direct PostgreSQL queries disabled. Use get_supabase() instead.")


async def check_database_connection() -> bool:
    """
    Legacy compatibility wrapper - redirects to Supabase connection check.
    """
    return await check_supabase_connection()

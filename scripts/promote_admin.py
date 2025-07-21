"""
Script to promote a user to admin role
Usage: python scripts/promote_admin.py <email>
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def promote_user_to_admin(email: str):
    """Promote a user to admin role"""
    # Create simple engine for this script
    db_url = os.getenv("DB_CONNECTION_STRING")
    if not db_url:
        logger.error("DB_CONNECTION_STRING environment variable not found")
        return False

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(
            text("SELECT id, email, role FROM profiles WHERE email = :email"), {"email": email}
        )

        user = result.fetchone()

        if not user:
            logger.error(f"User with email {email} not found")
            return False

        user_id, user_email, current_role = user

        if current_role == "admin":
            logger.info(f"User {user_email} is already an admin")
            return True

        # Update role to admin
        await conn.execute(
            text("UPDATE profiles SET role = 'admin', updated_at = NOW() WHERE email = :email"),
            {"email": email},
        )

        logger.info(f"✅ Successfully promoted {user_email} from {current_role} to admin")
        return True


async def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]

    try:
        success = await promote_user_to_admin(email)
        if success:
            print(f"✅ User {email} has been promoted to admin")
        else:
            print(f"❌ Failed to promote user {email}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error promoting user: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

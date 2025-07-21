"""
Unified management CLI for bet-intel application
Consolidates frequently used scripts into a single command interface
"""

import asyncio
import logging
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import typer
from config import settings
from sqlalchemy import text

from db import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Unified management CLI for bet-intel application")

# Database Commands
db_app = typer.Typer(help="Database management commands")
app.add_typer(db_app, name="db")

# User Commands
user_app = typer.Typer(help="User management commands")
app.add_typer(user_app, name="user")

# System Commands
system_app = typer.Typer(help="System management commands")
app.add_typer(system_app, name="system")


@user_app.command("create-test-users")
def create_test_users(count: int = typer.Option(3, help="Number of test users to create")):
    """Create test users for each role level (free, subscriber, admin)"""

    async def _create_test_users():
        test_users = [
            {
                "email": "free-user@test.com",
                "role": "free",
                "subscription_status": "none",
                "description": "Free tier user with limited access",
            },
            {
                "email": "paid-user@test.com",
                "role": "subscriber",
                "subscription_status": "active",
                "description": "Premium subscriber with full access",
            },
            {
                "email": "admin-user@test.com",
                "role": "admin",
                "subscription_status": "active",
                "description": "Administrator with all privileges",
            },
        ]

        # Limit to requested count
        test_users = test_users[:count]

        async with engine.begin() as conn:
            typer.echo("Creating test users...")

            for user in test_users:
                try:
                    # Check if user already exists
                    check_result = await conn.execute(
                        text("SELECT id FROM profiles WHERE email = :email"),
                        {"email": user["email"]},
                    )
                    existing = check_result.fetchone()

                    if existing:
                        # Update existing user
                        await conn.execute(
                            text(
                                """
                                UPDATE profiles
                                SET role = :role, subscription_status = :subscription_status
                                WHERE email = :email
                            """
                            ),
                            {
                                "email": user["email"],
                                "role": user["role"],
                                "subscription_status": user["subscription_status"],
                            },
                        )
                        typer.echo(f"✅ Updated {user['role']} user: {user['email']}")
                    else:
                        # Insert new user
                        await conn.execute(
                            text(
                                """
                                INSERT INTO profiles (id, email, role, subscription_status, created_at)
                                VALUES (gen_random_uuid(), :email, :role, :subscription_status, NOW())
                            """
                            ),
                            {
                                "email": user["email"],
                                "role": user["role"],
                                "subscription_status": user["subscription_status"],
                            },
                        )
                        typer.echo(f"✅ Created {user['role']} user: {user['email']}")

                except Exception as e:
                    typer.echo(f"❌ Failed to create user {user['email']}: {e}", err=True)
                    raise

            typer.echo(f"\n🎉 Successfully created {len(test_users)} test users!")

    asyncio.run(_create_test_users())


@user_app.command("promote-admin")
def promote_admin(
    email: str = typer.Argument(help="Email of user to promote to admin"),
):
    """Promote a user to admin role"""

    async def _promote_admin():
        async with engine.begin() as conn:
            # Check if user exists
            result = await conn.execute(
                text("SELECT id, email, role FROM profiles WHERE email = :email"),
                {"email": email},
            )

            user = result.fetchone()

            if not user:
                typer.echo(f"❌ User with email {email} not found", err=True)
                raise typer.Exit(1)

            user_id, user_email, current_role = user

            if current_role == "admin":
                typer.echo(f"ℹ️  User {user_email} is already an admin")
                return

            # Update role to admin
            await conn.execute(
                text("UPDATE profiles SET role = 'admin', updated_at = NOW() WHERE email = :email"),
                {"email": email},
            )

            typer.echo(f"✅ Successfully promoted {user_email} from {current_role} to admin")

    asyncio.run(_promote_admin())


@db_app.command("check")
def db_check():
    """Check database connectivity and basic health"""

    async def _check_db():
        try:
            async with engine.begin() as conn:
                # Test basic connectivity
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

                # Check profiles table
                result = await conn.execute(text("SELECT COUNT(*) FROM profiles"))
                user_count = result.fetchone()[0]

                typer.echo("✅ Database connectivity: OK")
                typer.echo(f"✅ Profiles table: {user_count} users")

        except Exception as e:
            typer.echo(f"❌ Database check failed: {e}", err=True)
            raise typer.Exit(1)

    asyncio.run(_check_db())


@system_app.command("config")
def show_config():
    """Show current configuration settings"""
    typer.echo("🔧 Current Configuration:")
    typer.echo("-" * 40)
    typer.echo(f"Environment: {settings.app_env}")
    typer.echo(f"Debug Mode: {settings.debug or settings.debug_mode}")
    typer.echo(f"Redis URL: {settings.redis_url}")
    typer.echo(
        f"Database URL: {'***configured***' if settings.db_connection_string else 'Not set'}"
    )
    typer.echo(f"Odds API Key: {'***configured***' if settings.odds_api_key else 'Not set'}")
    typer.echo(f"Refresh Interval: {settings.refresh_interval_minutes} minutes")


@system_app.command("verify")
def verify_system():
    """Verify system components are working"""

    async def _verify():
        typer.echo("🔍 System Verification")
        typer.echo("-" * 40)

        # Check database
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            typer.echo("✅ Database: Connected")
        except Exception as e:
            typer.echo(f"❌ Database: {e}")
            return False

        # Check Redis (if configured)
        try:
            from common.redis_utils import test_redis_connection

            if await test_redis_connection():
                typer.echo("✅ Redis: Connected")
            else:
                typer.echo("❌ Redis: Connection failed")
        except Exception as e:
            typer.echo(f"❌ Redis: {e}")

        # Check configuration
        missing_config = []
        if not settings.odds_api_key:
            missing_config.append("ODDS_API_KEY")
        if not settings.db_connection_string:
            missing_config.append("DB_CONNECTION_STRING")

        if missing_config:
            typer.echo(f"⚠️  Missing config: {', '.join(missing_config)}")
        else:
            typer.echo("✅ Configuration: Complete")

        typer.echo("\n🎉 System verification complete")
        return True

    asyncio.run(_verify())


if __name__ == "__main__":
    app()

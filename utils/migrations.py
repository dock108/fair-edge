"""
Database Migration Utilities
Handles automatic Alembic migration execution on application startup
"""

import asyncio
import logging
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations for Fair-Edge application"""

    def __init__(self, database_url: str = None):
        """
        Initialize migration manager

        Args:
            database_url: Database connection string
        """
        self.database_url = (
            database_url or os.getenv("DATABASE_URL") or os.getenv("DB_CONNECTION_STRING")
        )
        self.alembic_config_path = Path(__file__).parent.parent / "alembic.ini"

        if not self.database_url:
            raise ValueError("Database URL not provided and not found in environment variables")

        # Convert to async URL if needed
        if not self.database_url.startswith("postgresql+asyncpg://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    def get_alembic_config(self) -> Config:
        """Get Alembic configuration"""
        if not self.alembic_config_path.exists():
            raise FileNotFoundError(f"Alembic config not found at {self.alembic_config_path}")

        config = Config(str(self.alembic_config_path))

        # Set the database URL in the config
        sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        config.set_main_option("sqlalchemy.url", sync_url)

        return config

    async def check_database_connection(self) -> bool:
        """Check if database is accessible"""
        try:
            engine = create_async_engine(self.database_url)
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def get_current_revision(self) -> str:
        """Get current database revision"""
        try:
            # Use sync engine for Alembic operations
            sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")

            from sqlalchemy import create_engine

            engine = create_engine(sync_url)

            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()

            engine.dispose()
            return current_rev

        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None

    def get_head_revision(self) -> str:
        """Get the latest available revision"""
        try:
            config = self.get_alembic_config()
            script_dir = ScriptDirectory.from_config(config)
            return script_dir.get_current_head()
        except Exception as e:
            logger.error(f"Failed to get head revision: {e}")
            return None

    def is_migration_needed(self) -> bool:
        """Check if migration is needed"""
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()

            if current is None:
                logger.info("No current revision found - migration needed")
                return True

            if head is None:
                logger.warning("No head revision found - no migrations available")
                return False

            if current != head:
                logger.info(f"Migration needed: current={current}, head={head}")
                return True

            logger.info("Database is up to date")
            return False

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False

    def run_migrations(self, target_revision: str = "head") -> bool:
        """
        Run database migrations

        Args:
            target_revision: Target revision to migrate to (default: "head")

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self.get_alembic_config()

            logger.info(f"Running migrations to revision: {target_revision}")

            # Run the migration
            command.upgrade(config, target_revision)

            logger.info("Migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    async def run_migrations_async(self, target_revision: str = "head") -> bool:
        """
        Run migrations in a separate thread to avoid blocking async operations

        Args:
            target_revision: Target revision to migrate to (default: "head")

        Returns:
            bool: True if successful, False otherwise
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_migrations, target_revision)

    async def initialize_database(self, run_migrations: bool = True) -> bool:
        """
        Initialize database with migrations

        Args:
            run_migrations: Whether to run migrations automatically

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check database connection
            if not await self.check_database_connection():
                logger.error("Cannot connect to database")
                return False

            # Check if migrations are needed
            if not run_migrations:
                logger.info("Migration execution disabled")
                return True

            if not self.is_migration_needed():
                logger.info("No migrations needed")
                return True

            # Run migrations
            success = await self.run_migrations_async()

            if success:
                logger.info("Database initialization completed successfully")
            else:
                logger.error("Database initialization failed")

            return success

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration

        Args:
            message: Migration message
            autogenerate: Whether to autogenerate the migration

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self.get_alembic_config()

            if autogenerate:
                command.revision(config, message=message, autogenerate=True)
            else:
                command.revision(config, message=message)

            logger.info(f"Migration created: {message}")
            return True

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False


# Global migration manager instance
_migration_manager = None


def get_migration_manager() -> MigrationManager:
    """Get or create migration manager instance"""
    global _migration_manager

    if _migration_manager is None:
        _migration_manager = MigrationManager()

    return _migration_manager


async def run_startup_migrations() -> bool:
    """
    Run migrations on application startup
    Controlled by RUN_MIGRATIONS environment variable

    Returns:
        bool: True if successful or skipped, False if failed
    """
    # Check if migrations should be run
    run_migrations = os.getenv("RUN_MIGRATIONS", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    if not run_migrations:
        logger.info("Migrations disabled (RUN_MIGRATIONS=false)")
        return True

    try:
        manager = get_migration_manager()
        return await manager.initialize_database(run_migrations=True)
    except Exception as e:
        logger.error(f"Startup migrations failed: {e}")
        return False


# CLI functions for manual migration management
def migrate_database():
    """CLI function to run migrations manually"""
    import asyncio

    async def run():
        manager = get_migration_manager()
        return await manager.initialize_database(run_migrations=True)

    success = asyncio.run(run())

    if success:
        print("✅ Database migrations completed successfully")
    else:
        print("❌ Database migrations failed")
        exit(1)


def check_migration_status():
    """CLI function to check migration status"""
    try:
        manager = get_migration_manager()

        current = manager.get_current_revision()
        head = manager.get_head_revision()

        print(f"Current revision: {current or 'None'}")
        print(f"Head revision: {head or 'None'}")

        if manager.is_migration_needed():
            print("⚠️  Migration needed")
        else:
            print("✅ Database is up to date")

    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        exit(1)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd_arg = sys.argv[1]

        if cmd_arg == "migrate":
            migrate_database()
        elif cmd_arg == "status":
            check_migration_status()
        else:
            print("Usage: python migrations.py [migrate|status]")
    else:
        print("Usage: python migrations.py [migrate|status]")

#!/usr/bin/env python3
"""Run database migration to create users table."""

import sys
from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings


def run_migration():
    """Create users table if it doesn't exist."""
    migration_sql = """
    -- Create users table for authentication
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create index on email for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """
    
    try:
        print(f"Connecting to database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'database'}")
        with engine.begin() as conn:
            print("Running migration...")
            conn.execute(text(migration_sql))
            print("✅ Migration completed successfully!")
            print("✅ Users table created")
            return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_migration())

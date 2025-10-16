#!/usr/bin/env python3
"""
Database setup script.
Run this to initialize the database with tables and migrations.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.config import init_db, engine
from sqlalchemy import text


async def setup_database():
    """Setup database and run migrations."""
    try:
        print("Setting up database...")
        
        # Enable UUID extension
        async with engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            print("✓ UUID extension enabled")
        
        # Initialize database tables
        await init_db()
        print("✓ Database tables created")
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    
    return True


async def main():
    success = await setup_database()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

"""Migration script: add nfs_json column to cte_cliente if missing.

Usage:
    python scripts/add_nfs_json_migration.py

This script will connect using the project's async SQLAlchemy engine and add the column
in a safe way by first checking for its existence.
"""
import asyncio
from sqlalchemy import text

# Ensure project root is on sys.path so scripts can import the 'app' package
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import async_engine


async def main():
    async with async_engine.connect() as conn:
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'cte_cliente' AND column_name = 'nfs_json'"
        ))
        row = result.fetchone()
        
        if row:
            print("Column 'nfs_json' already exists on 'cte_cliente'. Nothing to do.")
            return

        dialect = async_engine.dialect.name
        print(f"Detected dialect: {dialect}. Adding 'nfs_json' column...")

        stmt = text('ALTER TABLE cte_cliente ADD COLUMN nfs_json TEXT')
        await conn.execute(stmt)
        await conn.commit()

    print("Migration complete: column 'nfs_json' added.")


if __name__ == '__main__':
    asyncio.run(main())

"""Migration script: add nfs_json column to cte_cliente if missing.

Usage:
    python scripts/add_nfs_json_migration.py

This script will connect using the project's SQLAlchemy engine and add the column
in a safe way by first checking for its existence.
"""
from sqlalchemy import inspect, text

# Ensure project root is on sys.path so scripts can import the 'app' package
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import engine


def main():
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('cte_cliente')]

    if 'nfs_json' in cols:
        print("Column 'nfs_json' already exists on 'cte_cliente'. Nothing to do.")
        return

    dialect = engine.dialect.name
    print(f"Detected dialect: {dialect}. Adding 'nfs_json' column...")

    if dialect == 'sqlite':
        # SQLite supports ADD COLUMN with default NULL
        stmt = text('ALTER TABLE cte_cliente ADD COLUMN nfs_json TEXT')
    else:
        # Postgres and others
        stmt = text('ALTER TABLE cte_cliente ADD COLUMN nfs_json TEXT')

    with engine.begin() as conn:
        conn.execute(stmt)

    print("Migration complete: column 'nfs_json' added.")


if __name__ == '__main__':
    main()

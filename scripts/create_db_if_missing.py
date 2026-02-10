#!/usr/bin/env python3
"""
Create the target Postgres database if it does not exist.
Intended for development convenience when AUTO_CREATE_DB=true.
"""
import os
import sys
import psycopg2
from psycopg2 import sql


def main():
    auto = os.getenv("AUTO_CREATE_DB", "false").lower()
    if auto not in ("1", "true", "yes"):
        print("AUTO_CREATE_DB not enabled; skipping DB creation.")
        return

    host = os.getenv("POSTGRES_HOST", "postgres")
    port = int(os.getenv("POSTGRES_PORT", 5432))
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    dbname = os.getenv("POSTGRES_DB", "postgres")
    maint_db = os.getenv("POSTGRES_MAINTENANCE_DB", "postgres")

    try:
        conn = psycopg2.connect(dbname=maint_db, user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cur.fetchone() is not None
        if exists:
            print(f"Database '{dbname}' already exists; nothing to do.")
        else:
            print(f"Creating database '{dbname}' ...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print("Database created.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Error while creating database:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

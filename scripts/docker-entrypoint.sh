#!/usr/bin/env sh
set -e

# Optionally create DB if AUTO_CREATE_DB=true
if [ "${AUTO_CREATE_DB}" = "true" ] || [ "${AUTO_CREATE_DB}" = "1" ]; then
  echo "AUTO_CREATE_DB enabled: attempting to create database if missing..."
  python scripts/create_db_if_missing.py || {
    echo "Database creation failed; continuing startup (you may need to fix permissions)."
  }
fi

# Execute the main container command
exec "$@"

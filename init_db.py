# Script para inicializar o banco de dados
# Uso: python init_db.py

import asyncio
from app.core.database import ensure_db_initialized


async def main():
    """Initialize database tables."""
    await ensure_db_initialized()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
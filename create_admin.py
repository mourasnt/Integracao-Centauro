# Script para criar usuário administrador inicial
# Uso: python create_admin.py

import asyncio
from app.core.database import AsyncSessionLocal, ensure_db_initialized
from app.models.user import User
from app.core.security import get_password_hash


async def create_admin():
    """Create admin user using async database session."""
    await ensure_db_initialized()
    
    async with AsyncSessionLocal() as db:
        admin = User(
            username="admin",
            email="admin@admin.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin user created successfully!")


if __name__ == "__main__":
    asyncio.run(create_admin())
# Crie um arquivo chamado create_admin.py na pasta backend/app

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@admin.com",
    hashed_password=get_password_hash("admin123"),
    is_active=True,
    is_admin=True
)
db.add(admin)
db.commit()
db.close()
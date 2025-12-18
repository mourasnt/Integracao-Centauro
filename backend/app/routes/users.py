from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.user import UserCreate, UserRead, UserLogin
from app.services.user_service import UserService
from app.models.user import User
from app.core.security import decode_access_token
from typing import List

router = APIRouter()
oauth2_scheme = HTTPBearer()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

def get_current_user(credentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
	token = credentials.credentials

	if not token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
	payload = decode_access_token(token)
	if not payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
	user = db.query(User).filter(User.username == payload.get("sub")).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
	return user

def require_admin(user: User = Depends(get_current_user)):
	if not user.is_admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas admin pode acessar.")
	return user

# Auth endpoint
@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
	token = UserService.login_for_access_token(db, user_login.username, user_login.password)
	if not token:
		raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
	return token

# User endpoints
@router.get("/users", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
	return db.query(User).all()

@router.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
	db_user = db.query(User).filter(User.id == user_id).first()
	if not db_user:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")
	db_user.username = user_update.username
	db_user.email = user_update.email
	db_user.hashed_password = db_user.hashed_password  # Não atualiza senha por padrão
	db_user.is_admin = user_update.is_admin
	db.commit()
	db.refresh(db_user)
	return db_user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
	db_user = db.query(User).filter(User.id == user_id).first()
	if not db_user:
		raise HTTPException(status_code=404, detail="Usuário não encontrado")
	db.delete(db_user)
	db.commit()

@router.post("/users", response_model=UserRead)
def create_new_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
	try:
		return UserService.create_user(db, user, current_user)
	except PermissionError:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas admin pode criar usuários.")

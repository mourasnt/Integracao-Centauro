
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token

class UserService:
	@staticmethod
	def authenticate_user(db: Session, username: str, password: str):
		user = db.query(User).filter(User.username == username).first()
		if not user or not verify_password(password, user.hashed_password):
			return None
		return user

	@staticmethod
	def login_for_access_token(db: Session, username: str, password: str):
		user = UserService.authenticate_user(db, username, password)
		if not user:
			return None
		access_token = create_access_token(data={"sub": user.username, "is_admin": user.is_admin})
		return {"access_token": access_token, "token_type": "bearer"}

	@staticmethod
	def create_user(db: Session, user: UserCreate, current_user: User):
		if not current_user.is_admin:
			raise PermissionError("Apenas admin pode criar usuários.")
		db_user = User(
			username=user.username,
			email=user.email,
			hashed_password=get_password_hash(user.password),
			is_admin=user.is_admin
		)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return db_user

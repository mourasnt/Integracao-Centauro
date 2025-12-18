from passlib.context import CryptContext  # type: ignore
import jwt
from jwt import InvalidTokenError
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
	return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	# PyJWT retorna bytes em versões antigas, garantir string
	if isinstance(encoded_jwt, bytes):
		encoded_jwt = encoded_jwt.decode('utf-8')
	return encoded_jwt

def decode_access_token(token: str):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		return payload
	except InvalidTokenError:
		return None

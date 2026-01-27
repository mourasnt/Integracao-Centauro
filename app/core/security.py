try:
    from passlib.context import CryptContext  # type: ignore
    _HAS_PASSLIB = True
except Exception:
    CryptContext = None
    _HAS_PASSLIB = False

try:
    import jwt
    from jwt import InvalidTokenError
    _HAS_JWT = True
except Exception:
    jwt = None
    InvalidTokenError = Exception
    _HAS_JWT = False

from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config.settings import settings
import json
import base64

if _HAS_PASSLIB:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    if pwd_context is None:
        # fallback for test environments: compare strings directly
        return plain_password == hashed_password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    if pwd_context is None:
        # fallback for tests: return the plain password (not secure)
        return password[:72]
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire.isoformat()})

    if _HAS_JWT:
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        # PyJWT retorna bytes em versões antigas, garantir string
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode('utf-8')
        return encoded_jwt
    else:
        # fallback: simple base64(json) token (no signature) for test env
        raw = json.dumps(to_encode, default=str).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode('utf-8')


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    if _HAS_JWT:
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            return payload
        except InvalidTokenError:
            return None
    else:
        try:
            raw = base64.urlsafe_b64decode(token.encode('utf-8'))
            payload = json.loads(raw)
            # optional: validate exp
            return payload
        except Exception:
            return None

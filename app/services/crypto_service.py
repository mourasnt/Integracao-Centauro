# app/services/crypto_service.py
import os
from typing import Optional

# cryptography is optional during tests (if not installed, crypto becomes a noop)
try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
    _HAS_FERNET = True
except Exception:
    Fernet = None
    InvalidToken = Exception
    _HAS_FERNET = False

from app.config.settings import FERNET_KEY as _FERNET_KEY

if _HAS_FERNET and not _FERNET_KEY:
    raise RuntimeError("FERNET_KEY não configurada no ambiente (.env)")

if _HAS_FERNET:
    fernet = Fernet(_FERNET_KEY.encode() if isinstance(_FERNET_KEY, str) else _FERNET_KEY)
else:
    fernet = None


def encrypt_text(plain: Optional[str]) -> Optional[str]:
    if plain is None:
        return None
    if plain == "":
        return ""
    if fernet is None:
        # fallback: return plain text when crypto unavailable (test-only behavior)
        return plain
    token = fernet.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    if token == "":
        return ""
    if fernet is None:
        # fallback: return token unchanged when crypto unavailable (test-only behavior)
        return token
    try:
        plain = fernet.decrypt(token.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken:
        # aqui você pode logar erro, gerar alerta etc.
        return None

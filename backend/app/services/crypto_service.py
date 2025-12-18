# app/services/crypto_service.py
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken #type: ignore
from app.config.settings import FERNET_KEY as _FERNET_KEY

if not _FERNET_KEY:
    raise RuntimeError("FERNET_KEY não configurada no ambiente (.env)")

fernet = Fernet(_FERNET_KEY.encode() if isinstance(_FERNET_KEY, str) else _FERNET_KEY)


def encrypt_text(plain: Optional[str]) -> Optional[str]:
    if plain is None:
        return None
    if plain == "":
        return ""
    token = fernet.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    if token == "":
        return ""
    try:
        plain = fernet.decrypt(token.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken:
        # aqui você pode logar erro, gerar alerta etc.
        return None

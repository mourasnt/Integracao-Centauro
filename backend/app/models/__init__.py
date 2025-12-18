# app/models/__init__.py
from .base import Base
from .user import User
from .carga import Carga
from .cte_cliente import CTeCliente
from .cte_subcontratacao import CTeSubcontratacao
from .agendamento import Agendamento
from .localidade import Estado, Municipio

__all__ = [
    "Base",
    "User",
    "Carga",
    "CTeCliente",
    "CTeSubcontratacao",
    "Agendamento",
    "Estado",
    "Municipio",
]

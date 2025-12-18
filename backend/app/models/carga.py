# app/models/carga.py
from __future__ import annotations

import uuid
import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import String, Enum as PgEnum

from app.services.constants import VALID_CODES
from .base import Base


class CargaStatus(BaseModel):
    code: str
    message: str
    type: str

    @field_validator("code")
    def validate_code(cls, v):
        if v not in VALID_CODES:
            raise ValueError(f"Código de status inválido: {v}")
        return v


class Carga(Base):
    __tablename__ = "cargas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    id_3zx: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )

    id_cliente: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )

    # rota
    origem_uf: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    origem_municipio: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    destino_uf: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    destino_municipio: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # status
    status: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"code": "10", **VALID_CODES["10"]},
    )

    # timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )

    # relacionamentos
    from app.models.cte_cliente import CTeCliente  # evitar import circular
    ctes_cliente: Mapped[List["CTeCliente"]] = relationship(
        back_populates="carga",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    from app.models.cte_subcontratacao import CTeSubcontratacao  # evitar import circular
    ctes_subcontratacao: Mapped[List["CTeSubcontratacao"]] = relationship(
        back_populates="carga",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


    from app.models.agendamento import Agendamento  # evitar import circular
    agendamento: Mapped[Optional["Agendamento"]] = relationship(
        back_populates="carga",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

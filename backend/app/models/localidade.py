from __future__ import annotations
import uuid
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INTEGER
from sqlalchemy import String, ForeignKey

from .base import Base


class Estado(Base):
    __tablename__ = "estados"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    nome: Mapped[str] = mapped_column(String, nullable=False)
    sigla: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    codigo_ibge: Mapped[int] = mapped_column(INTEGER, unique=True, nullable=False)

    municipios: Mapped[List["Municipio"]] = relationship(
        back_populates="estado", cascade="all, delete-orphan"
    )


class Municipio(Base):
    __tablename__ = "municipios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    nome: Mapped[str] = mapped_column(String, nullable=False)
    codigo_ibge: Mapped[int] = mapped_column(INTEGER, unique=True, nullable=False)

    estado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estados.id", ondelete="CASCADE")
    )

    estado: Mapped["Estado"] = relationship(back_populates="municipios")

# app/models/cte_subcontratacao.py
from __future__ import annotations

import uuid
import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, ForeignKey

from .base import Base
from app.services.crypto_service import encrypt_text, decrypt_text


class CTeSubcontratacao(Base):
    __tablename__ = "cte_subcontratacao"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    carga_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cargas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chave: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    xml_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

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
    carga: Mapped["Carga"] = relationship(
        back_populates="ctes_subcontratacao"
    )

    @property
    def xml(self) -> Optional[str]:
        return decrypt_text(self.xml_encrypted)

    @xml.setter
    def xml(self, value: Optional[str]) -> None:
        self.xml_encrypted = encrypt_text(value)

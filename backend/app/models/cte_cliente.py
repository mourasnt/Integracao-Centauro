# app/models/cte_cliente.py
from __future__ import annotations

import uuid
import datetime
from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, ForeignKey

from .base import Base
from app.services.crypto_service import encrypt_text, decrypt_text


class CTeCliente(Base):
    __tablename__ = "cte_cliente"

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
        String(60),  # 44 já basta, deixei folga
        nullable=False,
        index=True,
        unique=False,
    )

    # XML criptografado
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
        back_populates="ctes_cliente"
    )

    from app.models.tracking import Tracking  # evitar import circular
    trackings: Mapped[list["Tracking"]] = relationship(
        back_populates="cte_cliente",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Armazenamento de NFs associado a este CT-e como JSON no banco
    nfs_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    @property
    def nfs(self) -> list:
        import json
        if not self.nfs_json:
            return []
        try:
            return json.loads(self.nfs_json)
        except Exception:
            return []

    @nfs.setter
    def nfs(self, value: list) -> None:
        import json
        try:
            self.nfs_json = json.dumps(value or [])
        except Exception:
            self.nfs_json = None

    # propriedades convenientes
    @property
    def xml(self) -> Optional[str]:
        return decrypt_text(self.xml_encrypted)

    @xml.setter
    def xml(self, value: Optional[str]) -> None:
        self.xml_encrypted = encrypt_text(value)
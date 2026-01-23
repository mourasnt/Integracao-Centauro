# app/models/subcontracted_cte.py
"""
SubcontractedCTe model (formerly CTeSubcontratacao).
Represents a CTe document from subcontractors.
"""

from __future__ import annotations

import uuid
import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, ForeignKey

from .base import Base, TimestampMixin, EncryptedXMLMixin

if TYPE_CHECKING:
    from .shipment import Shipment


class SubcontractedCTe(Base, TimestampMixin, EncryptedXMLMixin):
    """
    Subcontracted CTe document model.
    
    Stores CTe documents from subcontractors with encrypted XML storage
    and VBLOG upload status tracking.
    
    Relationships:
        - shipment: Parent shipment
    """
    __tablename__ = "subcontracted_ctes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    access_key: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
        comment="CTe access key (44 digits)",
    )

    # VBLOG upload status
    vblog_status_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    vblog_status_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    vblog_raw_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    vblog_attempts: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    vblog_received_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        default=None,
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="subcontracted_ctes",
    )

    # Legacy property aliases
    @property
    def chave(self) -> str:
        """Legacy alias for access_key."""
        return self.access_key

    @chave.setter
    def chave(self, value: str) -> None:
        self.access_key = value

    @property
    def carga_id(self) -> uuid.UUID:
        """Legacy alias for shipment_id."""
        return self.shipment_id

    @property
    def carga(self):
        """Legacy alias for shipment."""
        return self.shipment

    @property
    def vblog_status_desc(self) -> Optional[str]:
        """Legacy alias for vblog_status_description."""
        return self.vblog_status_description

    @vblog_status_desc.setter
    def vblog_status_desc(self, value: Optional[str]) -> None:
        self.vblog_status_description = value

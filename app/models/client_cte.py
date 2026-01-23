# app/models/client_cte.py
"""
ClientCTe model (formerly CTeCliente).
Represents a CTe document received from the client.
"""

from __future__ import annotations

import uuid
import json
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, ForeignKey

from .base import Base, TimestampMixin, EncryptedXMLMixin

if TYPE_CHECKING:
    from .shipment import Shipment
    from .tracking_event import TrackingEvent


class ClientCTe(Base, TimestampMixin, EncryptedXMLMixin):
    """
    Client CTe document model.
    
    Stores CTe documents received from the client with encrypted XML storage.
    
    Relationships:
        - shipment: Parent shipment
        - tracking_events: Associated tracking events
    """
    __tablename__ = "client_ctes"

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

    # NF-e references stored as JSON
    invoices_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Associated NF-e keys as JSON array",
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="client_ctes",
    )

    tracking_events: Mapped[List["TrackingEvent"]] = relationship(
        "TrackingEvent",
        back_populates="client_cte",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def invoices(self) -> list:
        """Get list of associated NF-e keys."""
        if not self.invoices_json:
            return []
        try:
            return json.loads(self.invoices_json)
        except Exception:
            return []

    @invoices.setter
    def invoices(self, value: list) -> None:
        """Set list of associated NF-e keys."""
        try:
            self.invoices_json = json.dumps(value or [])
        except Exception:
            self.invoices_json = None

    # Legacy property aliases
    @property
    def chave(self) -> str:
        """Legacy alias for access_key."""
        return self.access_key

    @chave.setter
    def chave(self, value: str) -> None:
        self.access_key = value

    @property
    def nfs(self) -> list:
        """Legacy alias for invoices."""
        return self.invoices

    @nfs.setter
    def nfs(self, value: list) -> None:
        self.invoices = value

    @property
    def nfs_json(self) -> Optional[str]:
        """Legacy alias for invoices_json."""
        return self.invoices_json

    @nfs_json.setter
    def nfs_json(self, value: Optional[str]) -> None:
        self.invoices_json = value

    @property
    def carga_id(self) -> uuid.UUID:
        """Legacy alias for shipment_id."""
        return self.shipment_id

    @property
    def carga(self):
        """Legacy alias for shipment."""
        return self.shipment

    @property
    def trackings(self) -> List["TrackingEvent"]:
        """Legacy alias for tracking_events."""
        return self.tracking_events

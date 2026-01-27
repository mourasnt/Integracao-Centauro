# app/models/tracking_event.py
"""
TrackingEvent model (formerly Tracking).
Represents a tracking event for a CTe document.
"""

from __future__ import annotations

import uuid
import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime, ForeignKey

from .base import Base

if TYPE_CHECKING:
    from .client_cte import ClientCTe


class TrackingEvent(Base):
    """
    Tracking event model.
    
    Records tracking events sent to external systems (VBLOG/Brudam)
    for a specific CTe document.
    
    Relationships:
        - client_cte: Parent CTe document
    """
    __tablename__ = "tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    client_cte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("client_ctes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invoice_key: Mapped[Optional[str]] = mapped_column(
        String(60),
        nullable=True,
        index=True,
        comment="NF-e key this event applies to (null = all invoices in CTe)",
    )

    event_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Brudam/VBLOG event code",
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Event description",
    )

    event_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the event occurred",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationship
    client_cte: Mapped["ClientCTe"] = relationship(
        "ClientCTe",
        back_populates="tracking_events",
    )

    # Legacy property aliases
    @property
    def cte_cliente_id(self) -> uuid.UUID:
        """Legacy alias for client_cte_id."""
        return self.client_cte_id

    @property
    def cte_cliente(self):
        """Legacy alias for client_cte."""
        return self.client_cte

    @property
    def codigo_evento(self) -> str:
        """Legacy alias for event_code."""
        return self.event_code

    @codigo_evento.setter
    def codigo_evento(self, value: str) -> None:
        self.event_code = value

    @property
    def descricao(self) -> str:
        """Legacy alias for description."""
        return self.description

    @descricao.setter
    def descricao(self, value: str) -> None:
        self.description = value

    @property
    def data_evento(self) -> datetime.datetime:
        """Legacy alias for event_date."""
        return self.event_date

    @data_evento.setter
    def data_evento(self, value: datetime.datetime) -> None:
        self.event_date = value

# app/models/schedule.py
"""
Schedule model (formerly Agendamento).
Represents delivery schedule with ETA/ETD timestamps.
"""

from __future__ import annotations

import uuid
import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, ForeignKey

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .shipment import Shipment


class Schedule(Base, TimestampMixin):
    """
    Delivery schedule model.
    
    Tracks ETA (Estimated Time of Arrival) and ETD (Estimated Time of Departure)
    with scheduled, actual, and completion timestamps.
    
    Relationships:
        - shipment: Parent shipment (1:1)
    """
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1:1 relationship
    )

    # ETA (Estimated Time of Arrival) - Destination
    eta_scheduled: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled arrival time",
    )
    eta_actual: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual arrival time",
    )
    eta_departure: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Departure from destination",
    )

    # ETD (Estimated Time of Departure) - Origin
    etd_scheduled: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled departure time",
    )
    etd_actual: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual departure time",
    )
    etd_completed: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Loading completed time",
    )

    # Relationship
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="schedule",
    )

    # Legacy property aliases
    @property
    def carga_id(self) -> uuid.UUID:
        """Legacy alias for shipment_id."""
        return self.shipment_id

    @property
    def carga(self):
        """Legacy alias for shipment."""
        return self.shipment

    @property
    def eta_programado(self) -> Optional[datetime.datetime]:
        """Legacy alias for eta_scheduled."""
        return self.eta_scheduled

    @eta_programado.setter
    def eta_programado(self, value: Optional[datetime.datetime]) -> None:
        self.eta_scheduled = value

    @property
    def eta_realizado(self) -> Optional[datetime.datetime]:
        """Legacy alias for eta_actual."""
        return self.eta_actual

    @eta_realizado.setter
    def eta_realizado(self, value: Optional[datetime.datetime]) -> None:
        self.eta_actual = value

    @property
    def eta_saida(self) -> Optional[datetime.datetime]:
        """Legacy alias for eta_departure."""
        return self.eta_departure

    @eta_saida.setter
    def eta_saida(self, value: Optional[datetime.datetime]) -> None:
        self.eta_departure = value

    @property
    def etd_programado(self) -> Optional[datetime.datetime]:
        """Legacy alias for etd_scheduled."""
        return self.etd_scheduled

    @etd_programado.setter
    def etd_programado(self, value: Optional[datetime.datetime]) -> None:
        self.etd_scheduled = value

    @property
    def etd_realizado(self) -> Optional[datetime.datetime]:
        """Legacy alias for etd_actual."""
        return self.etd_actual

    @etd_realizado.setter
    def etd_realizado(self, value: Optional[datetime.datetime]) -> None:
        self.etd_actual = value

    @property
    def etd_finalizado(self) -> Optional[datetime.datetime]:
        """Legacy alias for etd_completed."""
        return self.etd_completed

    @etd_finalizado.setter
    def etd_finalizado(self, value: Optional[datetime.datetime]) -> None:
        self.etd_completed = value

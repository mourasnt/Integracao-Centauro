# app/models/shipment.py
"""
Shipment model (formerly Carga).
 Represents a cargo shipment with associated CTes.
"""

from __future__ import annotations

import uuid
import datetime
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import String

from app.services.constants import VALID_CODES
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .client_cte import ClientCTe
    from .subcontracted_cte import SubcontractedCTe


class ShipmentStatus(BaseModel):
    """
    Shipment status with automatic validation and field population.
    """
    code: str
    message: Optional[str] = None
    type: Optional[str] = None

    @field_validator("code")
    def validate_code(cls, v):
        if v not in VALID_CODES:
            raise ValueError(f"Invalid status code: {v}")
        return v

    @model_validator(mode="after")
    def fill_from_code(self):
        info = VALID_CODES.get(self.code)
        if info:
            if not self.message:
                self.message = info.get("message")
            if not self.type:
                self.type = info.get("type")
        return self


class Shipment(Base, TimestampMixin):
    """
    Shipment model representing a cargo transport.
    
    Relationships:
        - client_ctes: CTe documents from the client
        - subcontracted_ctes: CTe documents from subcontractors
    """
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    external_id: Mapped[Optional[str]] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=True,
        comment="External system ID (formerly id_3zx)",
    )

    client_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Client reference ID",
    )

    # Route information (JSON for flexibility)
    origin_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    origin_city: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    destination_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    destination_city: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status (JSON containing code, message, type)
    status: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"code": "10", **VALID_CODES["10"]},
    )

    # Relationships
    client_ctes: Mapped[List["ClientCTe"]] = relationship(
        "ClientCTe",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    subcontracted_ctes: Mapped[List["SubcontractedCTe"]] = relationship(
        "SubcontractedCTe",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )



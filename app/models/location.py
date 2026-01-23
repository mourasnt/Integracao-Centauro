# app/models/location.py
"""
Location models (formerly Estado/Municipio).
Represents Brazilian states and municipalities.
"""

from __future__ import annotations

import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Integer, ForeignKey

from .base import Base

if TYPE_CHECKING:
    pass


class State(Base):
    """
    Brazilian state model.
    
    Relationships:
        - municipalities: Cities in this state
    """
    __tablename__ = "states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="State name",
    )

    abbreviation: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        unique=True,
        comment="Two-letter state code (e.g., SP, RJ)",
    )

    ibge_code: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        comment="IBGE state code",
    )

    # Relationship
    municipalities: Mapped[List["Municipality"]] = relationship(
        "Municipality",
        back_populates="state",
        cascade="all, delete-orphan",
    )

    # Legacy property aliases
    @property
    def nome(self) -> str:
        """Legacy alias for name."""
        return self.name

    @nome.setter
    def nome(self, value: str) -> None:
        self.name = value

    @property
    def sigla(self) -> str:
        """Legacy alias for abbreviation."""
        return self.abbreviation

    @sigla.setter
    def sigla(self, value: str) -> None:
        self.abbreviation = value

    @property
    def codigo_ibge(self) -> int:
        """Legacy alias for ibge_code."""
        return self.ibge_code

    @codigo_ibge.setter
    def codigo_ibge(self, value: int) -> None:
        self.ibge_code = value

    @property
    def municipios(self) -> List["Municipality"]:
        """Legacy alias for municipalities."""
        return self.municipalities


class Municipality(Base):
    """
    Brazilian municipality (city) model.
    
    Relationships:
        - state: Parent state
    """
    __tablename__ = "municipalities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Municipality name",
    )

    ibge_code: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        comment="IBGE municipality code",
    )

    state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationship
    state: Mapped["State"] = relationship(
        "State",
        back_populates="municipalities",
    )

    # Legacy property aliases
    @property
    def nome(self) -> str:
        """Legacy alias for name."""
        return self.name

    @nome.setter
    def nome(self, value: str) -> None:
        self.name = value

    @property
    def codigo_ibge(self) -> int:
        """Legacy alias for ibge_code."""
        return self.ibge_code

    @codigo_ibge.setter
    def codigo_ibge(self, value: int) -> None:
        self.ibge_code = value

    @property
    def estado_id(self) -> uuid.UUID:
        """Legacy alias for state_id."""
        return self.state_id

    @property
    def estado(self) -> State:
        """Legacy alias for state."""
        return self.state

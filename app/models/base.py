# app/models/base.py
"""
Base classes and mixins for SQLAlchemy models.
"""

from __future__ import annotations
import uuid
import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Text, func

from app.services.crypto_service import encrypt_text, decrypt_text


class Base(DeclarativeBase):
    """Base declarative class for all models."""
    pass


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID."""
    return uuid.uuid4()


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    Use with multiple inheritance: class MyModel(Base, TimestampMixin)
    """
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class EncryptedXMLMixin:
    """
    Mixin for models that store encrypted XML content.
    Provides xml property that auto-encrypts/decrypts.
    
    Requires: xml_encrypted column in the model.
    """
    xml_encrypted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    @property
    def xml(self) -> Optional[str]:
        """Get decrypted XML content."""
        return decrypt_text(self.xml_encrypted)

    @xml.setter
    def xml(self, value: Optional[str]) -> None:
        """Set XML content (will be encrypted)."""
        self.xml_encrypted = encrypt_text(value)

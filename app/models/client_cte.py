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
from app.services.constants import VALID_CODES

if TYPE_CHECKING:
    from .shipment import Shipment
    from .tracking_event import TrackingEvent


class InvoiceStatus:
    """
    Helper class for invoice status operations.
    
    Each invoice is stored as: {"key": "35240...", "status": {"code": "1", "message": "...", "type": "..."}}
    """
    
    DEFAULT_CODE = "10"  # Initial status code
    
    @staticmethod
    def create(key: str, code: str = None) -> dict:
        """Create invoice object with key and status."""
        status_code = code or InvoiceStatus.DEFAULT_CODE
        status_info = VALID_CODES.get(status_code, {})
        return {
            "key": key,
            "status": {
                "code": status_code,
                "message": status_info.get("message", ""),
                "type": status_info.get("type", ""),
            }
        }
    
    @staticmethod
    def update_status(invoice: dict, code: str) -> dict:
        """Update invoice status in place and return it."""
        status_info = VALID_CODES.get(code, {})
        invoice["status"] = {
            "code": code,
            "message": status_info.get("message", ""),
            "type": status_info.get("type", ""),
        }
        return invoice
    
    @staticmethod
    def migrate_legacy(data: list) -> list:
        """Migrate legacy format (list of strings) to new format (list of dicts)."""
        if not data:
            return []
        # Check if already new format
        if data and isinstance(data[0], dict) and "key" in data[0]:
            return data
        # Migrate from old format
        return [InvoiceStatus.create(key) for key in data]


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
    def invoices(self) -> list[dict]:
        """Get list of invoices with individual status."""
        if not self.invoices_json:
            return []
        try:
            data = json.loads(self.invoices_json)
            # Auto-migrate legacy format
            return InvoiceStatus.migrate_legacy(data)
        except Exception:
            return []

    @invoices.setter
    def invoices(self, value: list) -> None:
        """Set list of invoices. Accepts both old format (strings) and new format (dicts)."""
        try:
            if value:
                # Migrate if needed
                migrated = InvoiceStatus.migrate_legacy(value)
                self.invoices_json = json.dumps(migrated)
            else:
                self.invoices_json = None
        except Exception:
            self.invoices_json = None

    @property
    def invoice_keys(self) -> list[str]:
        """Get just the invoice keys (for backward compatibility and filtering)."""
        return [inv["key"] if isinstance(inv, dict) else inv for inv in self.invoices]

    def get_invoice_by_key(self, key: str) -> Optional[dict]:
        """Get a specific invoice by its key."""
        for inv in self.invoices:
            if inv.get("key") == key:
                return inv
        return None

    def update_invoice_status(self, keys: Optional[list[str]], code: str) -> list[dict]:
        """
        Update status for specific invoices or all if keys is None.
        
        Args:
            keys: List of invoice keys to update, or None to update all
            code: New status code
            
        Returns:
            List of updated invoice objects
        """
        invoices = self.invoices
        keys_set = set(keys) if keys else None
        updated = []
        
        for inv in invoices:
            if keys_set is None or inv["key"] in keys_set:
                InvoiceStatus.update_status(inv, code)
                updated.append(inv)
        
        self.invoices_json = json.dumps(invoices)
        return updated

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

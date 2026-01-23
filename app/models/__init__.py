# app/models/__init__.py
"""
SQLAlchemy models package.
Exports all models for use throughout the application.
"""

from .base import Base, TimestampMixin, EncryptedXMLMixin
from .user import User

# Models (English names)
from .shipment import Shipment, ShipmentStatus
from .client_cte import ClientCTe
from .subcontracted_cte import SubcontractedCTe
from .schedule import Schedule
from .tracking_event import TrackingEvent
from .location import State, Municipality

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    "EncryptedXMLMixin",
    
    # User
    "User",
    
    "Shipment",
    "ShipmentStatus",
    "ClientCTe",
    "SubcontractedCTe",
    "Schedule",
    "TrackingEvent",
    "State",
    "Municipality",
]

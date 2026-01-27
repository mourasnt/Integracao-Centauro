# app/schemas/__init__.py
"""
Pydantic schemas package.
Exports all schemas for use throughout the application.
"""

# New schemas with English names
from .shipment import (
    ShipmentBase,
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentStatusInput,
    ShipmentRead,
    StateInfo,
    CityInfo,
)
from .client_cte import (
    ClientCTeBase,
    ClientCTeCreate,
    ClientCTeRead,
)
from .subcontracted_cte import (
    SubcontractedCTeBase,
    SubcontractedCTeCreate,
    SubcontractedCTeRead,
    SubcontractedCTeWithVBlog,
    VBlogParsedResponse,
)
from .tracking_event import (
    TrackingEventBase,
    TrackingEventCreate,
    TrackingEventRead,
)
from .location import (
    StateBase,
    StateRead,
    MunicipalityBase,
    MunicipalityRead,
)
from .user import (
    UserCreate,
    UserRead,
)

__all__ = [
    # Shipment
    "ShipmentBase",
    "ShipmentCreate",
    "ShipmentUpdate",
    "ShipmentStatusInput",
    "ShipmentRead",
    "StateInfo",
    "CityInfo",
    
    # Client CTe
    "ClientCTeBase",
    "ClientCTeCreate",
    "ClientCTeRead",
    
    # Subcontracted CTe
    "SubcontractedCTeBase",
    "SubcontractedCTeCreate",
    "SubcontractedCTeRead",
    "SubcontractedCTeWithVBlog",
    "VBlogParsedResponse",
    
    # Tracking
    "TrackingEventBase",
    "TrackingEventCreate",
    "TrackingEventRead",
    
    # Location
    "StateBase",
    "StateRead",
    "MunicipalityBase",
    "MunicipalityRead",
    
    # User
    "UserCreate",
    "UserRead",
    
]

# app/schemas/client_cte.py
"""
ClientCTe schemas (formerly cte_cliente.py).
Pydantic models for client CTe API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class ClientCTeBase(BaseModel):
    """Base client CTe schema."""
    access_key: str = Field(..., alias="chave")

    class Config:
        populate_by_name = True


class ClientCTeCreate(ClientCTeBase):
    """Schema for creating a client CTe."""
    xml: Optional[str] = None


class ClientCTeRead(ClientCTeBase):
    """Schema for reading a client CTe."""
    id: uuid.UUID
    shipment_id: uuid.UUID = Field(..., alias="carga_id")
    xml: Optional[str] = None
    invoices: Optional[List[str]] = Field(None, alias="nfs")

    class Config:
        from_attributes = True
        populate_by_name = True


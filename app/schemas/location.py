# app/schemas/location.py
"""
Location schemas (formerly localidade.py).
Pydantic models for state and municipality API endpoints.
"""

from pydantic import BaseModel, Field
import uuid


class StateBase(BaseModel):
    """Base state schema."""
    name: str = Field(..., alias="nome")
    abbreviation: str = Field(..., alias="sigla")
    ibge_code: int = Field(..., alias="codigo_ibge")

    class Config:
        populate_by_name = True


class StateRead(StateBase):
    """Schema for reading a state."""
    id: uuid.UUID

    class Config:
        from_attributes = True
        populate_by_name = True


class MunicipalityBase(BaseModel):
    """Base municipality schema."""
    name: str = Field(..., alias="nome")
    ibge_code: int = Field(..., alias="codigo_ibge")
    state_id: uuid.UUID = Field(..., alias="estado_id")

    class Config:
        populate_by_name = True


class MunicipalityRead(MunicipalityBase):
    """Schema for reading a municipality."""
    id: uuid.UUID

    class Config:
        from_attributes = True
        populate_by_name = True


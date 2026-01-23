# app/schemas/subcontracted_cte.py
"""
SubcontractedCTe schemas (formerly cte_subcontratacao.py).
Pydantic models for subcontracted CTe API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid


class SubcontractedCTeBase(BaseModel):
    """Base subcontracted CTe schema."""
    access_key: str = Field(..., alias="chave")

    class Config:
        populate_by_name = True


class SubcontractedCTeCreate(SubcontractedCTeBase):
    """Schema for creating a subcontracted CTe."""
    xml: Optional[str] = None


class SubcontractedCTeRead(SubcontractedCTeBase):
    """Schema for reading a subcontracted CTe."""
    id: uuid.UUID
    shipment_id: uuid.UUID = Field(..., alias="carga_id")
    xml: Optional[str] = None

    # VBLOG status fields
    vblog_status_code: Optional[str] = None
    vblog_status_description: Optional[str] = Field(None, alias="vblog_status_desc")
    vblog_raw_response: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class VBlogParsedResponse(BaseModel):
    """Parsed VBLOG response structure."""
    control: Optional[Dict[str, str]] = None
    docs: Optional[List[Dict[str, str]]] = None
    raw: Optional[str] = None
    sent: Optional[str] = None


class SubcontractedCTeWithVBlog(SubcontractedCTeRead):
    """SubcontractedCTe with parsed VBLOG response."""
    vblog_parsed: Optional[VBlogParsedResponse] = None


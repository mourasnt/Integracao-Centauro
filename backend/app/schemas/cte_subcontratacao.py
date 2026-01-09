# app/schemas/cte_subcontratacao.py
from pydantic import BaseModel
from typing import Optional
import uuid


class CTeSubBase(BaseModel):
    chave: str


class CTeSubCreate(CTeSubBase):
    xml: Optional[str] = None


from typing import Optional, List, Dict


class CTeSubRead(CTeSubBase):
    id: uuid.UUID
    carga_id: uuid.UUID
    xml: Optional[str] = None

    # VBLOG persistent fields (optional)
    vblog_status_code: Optional[str] = None
    vblog_status_desc: Optional[str] = None
    vblog_raw_response: Optional[str] = None

    class Config:
        from_attributes = True


class VBlogParsed(BaseModel):
    control: Optional[Dict[str, str]] = None
    docs: Optional[List[Dict[str, str]]] = None
    raw: Optional[str] = None
    sent: Optional[str] = None


class CTeSubWithVBlog(CTeSubRead):
    vblog_parsed: Optional[VBlogParsed] = None

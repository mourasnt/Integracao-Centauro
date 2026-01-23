# app/services/vblog/transito.py
"""
VBLOG Transit service for querying open transits.
Refactored from vblog_transito.py with shared base class.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
import xml.etree.ElementTree as ET

from app.utils.logger import logger
from .base import VBlogBaseClient, NS, NSMAP


# -----------------------
# Pydantic Models
# -----------------------
class Document(BaseModel):
    """Document reference in transit."""
    type: Optional[str] = None  # 'chaveCTe' or 'xml' or others
    value: Optional[str] = None  # text between tags (key) or None for empty element
    doc_end: Optional[str] = None
    operation_type: Optional[str] = None
    other_attrs: dict = Field(default_factory=dict)


class Driver(BaseModel):
    """Driver information."""
    cpf: Optional[str] = None
    name: Optional[str] = None
    other: dict = Field(default_factory=dict)


class Vehicle(BaseModel):
    """Vehicle information."""
    traction: Optional[str] = None
    trailer: Optional[str] = None
    other: dict = Field(default_factory=dict)


class RoadModal(BaseModel):
    """Road transport modal information."""
    driver: Optional[Driver] = None
    vehicle: Optional[Vehicle] = None
    other: dict = Field(default_factory=dict)


class TransitControl(BaseModel):
    """Transit control information."""
    transport_doc: Optional[str] = None
    docs: List[Document] = Field(default_factory=list)
    road_modal: Optional[RoadModal] = None
    other: dict = Field(default_factory=dict)


class TransitResponse(BaseModel):
    """Response from transit query."""
    code: Optional[int] = None
    description: Optional[str] = None
    protocol: Optional[str] = None
    transits: List[TransitControl] = Field(default_factory=list)
    raw_xml: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class VBlogTransitoService(VBlogBaseClient):
    """
    Service for querying open transits from VBLOG API.
    """

    def __init__(
        self,
        cnpj: Optional[str] = None,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        super().__init__(cnpj=cnpj, token=token, base_url=base_url, timeout=timeout)
        self.endpoint = f"{self.base_url}/Webapi/transito/aberto/v2" if self.base_url else None

    def build_request_xml(self, return_type: int = 7, transit_status: int = 2) -> str:
        """
        Build XML request for open transits query.
        
        Args:
            return_type: tpRet value (7 = all documents)
            transit_status: stTransito value (2 = open)
        """
        root = self._build_xml_envelope("envDocSubTransito")
        
        control = ET.SubElement(root, "Control")
        ET.SubElement(control, "tpRet").text = str(return_type)
        ET.SubElement(control, "stTransito").text = str(transit_status)
        
        return self._to_xml_string(root)

    async def send_xml(self, xml: str) -> str:
        """Send XML request and return response text."""
        if not self.endpoint:
            raise ValueError("VBLOG base URL not configured")
        
        success, response, status = await self._send_with_retry(
            url=self.endpoint,
            payload=xml,
            content_type="application/xml",
        )
        
        if not success and status >= 500:
            raise RuntimeError(f"VBLOG service error: {response[:200]}")
        
        return response

    def _safe_find_text(self, root: ET.Element, path: str) -> Optional[str]:
        """Safely find text in XML element."""
        elem = root.find(path, NSMAP)
        return elem.text.strip() if elem is not None and elem.text else None

    def parse_response(self, xml_text: str) -> TransitResponse:
        """
        Parse XML response into structured models.
        Resilient: missing fields result in None/empty lists.
        """
        result = TransitResponse(raw_xml=xml_text)

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            result.warnings.append(f"Invalid XML: {e}")
            return result

        # Code and description (Control)
        code_text = self._safe_find_text(root, ".//ns:Control/ns:Cod")
        try:
            result.code = int(code_text) if code_text and code_text.isdigit() else None
        except Exception:
            result.code = None

        result.description = self._safe_find_text(root, ".//ns:Control/ns:xDesc")
        result.protocol = self._safe_find_text(root, ".//ns:nProt")

        # Code 13 = no documents (not an error)
        if result.code == 13:
            result.warnings.append("Code 13 - No documents found")

        # Find all ControleTransito nodes
        control_nodes = root.findall(".//ns:ControleTransito", NSMAP)
        for ct_node in control_nodes:
            ct_model = TransitControl()
            ct_model.transport_doc = ct_node.attrib.get("xDocTransp")

            # Parse Docs within each ControleTransito
            docs_nodes = ct_node.findall(".//ns:Docs", NSMAP)
            for docs_node in docs_nodes:
                for child in list(docs_node):
                    tag = child.tag
                    local = tag.split("}", 1)[1] if "}" in tag else tag
                    
                    doc = Document(
                        type=local,
                        value=child.text.strip() if child.text else None,
                        doc_end=child.attrib.get("xDocFim"),
                        operation_type=child.attrib.get("tpOp"),
                        other_attrs={k: v for k, v in child.attrib.items() 
                                    if k not in ("xDocFim", "tpOp")},
                    )
                    ct_model.docs.append(doc)

                ct_model.other.update(docs_node.attrib)

            # Parse road modal (optional)
            modal_node = ct_node.find(".//ns:infModalRodoviario", NSMAP)
            if modal_node is not None:
                modal = RoadModal()
                
                cpf_node = modal_node.find(".//ns:CPFmotorista", NSMAP)
                name_node = modal_node.find(".//ns:NomeMotorista", NSMAP)
                
                driver = Driver()
                if cpf_node is not None and cpf_node.text:
                    driver.cpf = cpf_node.text.strip()
                if name_node is not None and name_node.text:
                    driver.name = name_node.text.strip()
                modal.driver = driver

                vehicle = Vehicle()
                traction_node = modal_node.find(".//ns:Tracao", NSMAP)
                trailer_node = modal_node.find(".//ns:Reboque", NSMAP)
                if traction_node is not None and traction_node.text:
                    vehicle.traction = traction_node.text.strip()
                if trailer_node is not None and trailer_node.text:
                    vehicle.trailer = trailer_node.text.strip()
                modal.vehicle = vehicle

                ct_model.road_modal = modal

            ct_model.other.update(ct_node.attrib)
            result.transits.append(ct_model)

        return result

    async def query_open_transits(
        self, 
        return_type: int = 7, 
        transit_status: int = 2
    ) -> TransitResponse:
        """
        Main method: build XML, send request, and parse response.
        Always returns a TransitResponse (even on errors).
        """
        xml = self.build_request_xml(return_type=return_type, transit_status=transit_status)
        
        try:
            response = await self.send_xml(xml)
        except Exception as e:
            logger.error(f"Transit query failed: {e}")
            ret = TransitResponse(raw_xml=None)
            ret.warnings.append(f"Request failed: {e}")
            return ret

        return self.parse_response(response)

    # Legacy method aliases for backward compatibility
    async def consultar_transito_aberto(self, tpRet: int = 7, stTransito: int = 2) -> TransitResponse:
        """Legacy alias for query_open_transits."""
        return await self.query_open_transits(return_type=tpRet, transit_status=stTransito)

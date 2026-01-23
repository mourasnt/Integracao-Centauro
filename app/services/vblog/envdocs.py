# app/services/vblog/envdocs.py
"""
VBLOG EnvDocs service for uploading CTe documents.
Refactored from vblog_envdocs_service.py with shared base class.
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict

from app.utils.logger import logger
from .base import VBlogBaseClient, NS


class VBlogEnvDocsService(VBlogBaseClient):
    """
    Service for uploading CTe documents to VBLOG API.
    """

    def __init__(self, vblog_client: VBlogBaseClient):
        """
        Initialize with parent VBLOG client to share configuration.
        
        Args:
            vblog_client: Parent VBlogTransitoService or similar
        """
        super().__init__(
            cnpj=vblog_client.cnpj,
            token=vblog_client.token,
            base_url=vblog_client.base_url,
            timeout=30.0,
        )
        self._parent_client = vblog_client
        self.endpoint = f"{self.base_url}/Webapi/envDocs/Upload/CTe" if self.base_url else None

    async def _get_client(self):
        """Share HTTP client with parent."""
        return await self._parent_client._get_client()

    def _clean_cte_string(self, raw: str) -> str:
        """
        Clean CTe XML string for embedding.
        
        Removes escape characters, XML declaration, and extra whitespace
        while preserving the core XML structure.
        """
        if not raw:
            return ""
        
        s = str(raw).strip()
        
        # Remove JSON escape characters
        s = s.replace('\\"', '"')
        s = s.replace('\\n', '')
        s = s.replace('\\r', '')
        s = s.replace('\\t', '')
        s = s.replace('\\', '')
        
        # Fix spacing in attributes
        s = re.sub(r'=\s+"', '="', s)
        
        # Remove XML declaration
        if s.startswith("<?xml"):
            idx = s.find("?>")
            if idx != -1:
                s = s[idx + 2:].strip()
        
        return s

    def build_upload_xml(self, cte_xmls: List[str]) -> str:
        """
        Build VBLOG envelope for CTe upload.
        
        Uses placeholder injection to preserve CTe XML structure exactly.
        
        Args:
            cte_xmls: List of CTe XML strings
            
        Returns:
            Complete envelope XML string
        """
        # Build envelope structure
        root = ET.Element(f"{{{NS}}}recepDocSub", {"versao": "1.00"})
        
        # Authentication
        autentic = ET.SubElement(root, f"{{{NS}}}Autentic")
        ET.SubElement(autentic, f"{{{NS}}}xCNPJ").text = re.sub(r'\D', '', str(self.cnpj))
        ET.SubElement(autentic, f"{{{NS}}}xToken").text = str(self.token)
        
        # Control with document groups
        control = ET.SubElement(root, f"{{{NS}}}Control")
        
        payloads = {}
        for idx, raw_cte in enumerate(cte_xmls):
            grupo = ET.SubElement(control, f"{{{NS}}}grupoDoc")
            xxml = ET.SubElement(grupo, f"{{{NS}}}xXMLCTe")
            
            # Create placeholder token
            token = f"___PAYLOAD_CTE_{idx}___"
            xxml.text = token
            
            # Clean and store actual content
            payloads[token] = self._clean_cte_string(raw_cte)
        
        # Generate envelope string
        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        
        # Fix namespace declaration
        xml_str = re.sub(
            r'<recepDocSub[^>]*>',
            f'<recepDocSub versao="1.00" xmlns="{NS}">',
            xml_str,
            count=1
        )
        
        # Inject actual CTe content
        for token, content in payloads.items():
            xml_str = xml_str.replace(token, content)
        
        return xml_str

    async def upload_ctes(self, cte_xmls: List[str]) -> Dict:
        """
        Upload CTe documents to VBLOG.
        
        Args:
            cte_xmls: List of CTe XML strings
            
        Returns:
            Parsed response dict
        """
        if not self.endpoint:
            raise ValueError("VBLOG base URL not configured")
        
        if not cte_xmls:
            return {"success": True, "message": "No documents to upload"}
        
        xml = self.build_upload_xml(cte_xmls)
        
        logger.info(f"Uploading {len(cte_xmls)} CTe(s) to VBLOG")
        
        success, response, status = await self._send_with_retry(
            url=self.endpoint,
            payload=xml,
            content_type="application/xml",
        )
        
        result = self.parse_response(response)
        result["http_status"] = status
        result["success"] = success
        
        if success:
            logger.info(f"CTe upload successful")
        else:
            logger.warning(f"CTe upload failed: {response[:200]}")
        
        return result

    def parse_response(self, response: str) -> Dict:
        """
        Parse VBLOG response (JSON or XML).
        
        Args:
            response: Response text
            
        Returns:
            Parsed response dict
        """
        if not response:
            return {"error": "Empty response"}
        
        # Try JSON first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try XML
        try:
            root = ET.fromstring(response)
            result = {}
            
            # Extract common fields
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag in ['Cod', 'codigo']:
                    result['code'] = elem.text
                elif tag in ['xDesc', 'descricao']:
                    result['description'] = elem.text
                elif tag in ['nProt', 'protocolo']:
                    result['protocol'] = elem.text
            
            return result
            
        except ET.ParseError:
            return {"raw": response[:500]}

    # Legacy method aliases
    def build_recep_doc_sub(self, xml_ctes: List[str]) -> str:
        """Legacy alias for build_upload_xml."""
        return self.build_upload_xml(xml_ctes)

    async def post_recep_doc_sub(self, xml: str, max_retries: int = 3) -> str:
        """Legacy method - use upload_ctes instead."""
        success, response, _ = await self._send_with_retry(
            url=self.endpoint,
            payload=xml,
            content_type="application/xml",
        )
        return response

    def parse_retrecep_doc_sub(self, xml_retorno: str) -> Optional[dict]:
        """Legacy alias for parse_response."""
        return self.parse_response(xml_retorno)

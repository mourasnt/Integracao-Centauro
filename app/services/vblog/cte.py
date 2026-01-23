# app/services/vblog/cte.py
"""
VBLOG CTe service for downloading CTe XML documents.
Refactored from vblog_cte_service.py with shared base class.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from app.utils.logger import logger
from .base import VBlogBaseClient, NS


class VBlogCTeService(VBlogBaseClient):
    """
    Service for downloading CTe documents from VBLOG API.
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
            timeout=30.0,  # Longer timeout for downloads
        )
        self._parent_client = vblog_client
        self.endpoint = f"{self.base_url}/Webapi/transito/cte/v2" if self.base_url else None

    async def _get_client(self):
        """Share HTTP client with parent."""
        return await self._parent_client._get_client()

    def build_cte_request_xml(self, access_key: str) -> str:
        """
        Build XML request for CTe download.
        
        Args:
            access_key: CTe access key (44 digits)
            
        Returns:
            XML string
        """
        return (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<envDocSubTransitoCTe versao="2.00" xmlns="{NS}">'
            f'<Autentic>'
            f'<xCNPJ>{self.cnpj}</xCNPJ>'
            f'<xToken>{self.token}</xToken>'
            f'</Autentic>'
            f'<Control>'
            f'<tpRet>3</tpRet>'
            f'<Docs>'
            f'<chaveCTe>{access_key}</chaveCTe>'
            f'</Docs>'
            f'</Control>'
            f'</envDocSubTransitoCTe>'
        )

    async def send_cte_request(self, xml: str) -> str:
        """Send CTe request and return response."""
        if not self.endpoint:
            raise ValueError("VBLOG base URL not configured")

        success, response, status = await self._send_with_retry(
            url=self.endpoint,
            payload=xml,
            content_type="application/xml",
        )

        if not success:
            logger.error(f"CTe download failed: HTTP {status}")
            raise RuntimeError(f"CTe download failed: {response[:200]}")

        return response

    def parse_cte_response(self, xml_response: str) -> Optional[str]:
        """
        Extract CTe XML from VBLOG response.
        
        Args:
            xml_response: VBLOG response XML
            
        Returns:
            CTe XML string or None if not found
        """
        if not xml_response:
            return None

        try:
            root = ET.fromstring(xml_response)
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return None

        # Check for API logical errors
        for elem in root.iter():
            if "Control" in elem.tag:
                code = elem.find(".//{*}Cod") or elem.find("Cod")
                desc = elem.find(".//{*}xDesc") or elem.find("xDesc")
                
                if code is not None and code.text not in ["001", "1"]:
                    msg = desc.text if desc is not None else "No description"
                    logger.warning(f"VBLOG API error: {msg}")

        # Search for CTe XML content
        possible_tags = ['xXMLCTe', 'xml', 'cteProc']
        
        for elem in root.iter():
            tag_clean = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if tag_clean in possible_tags:
                # Found the container element
                if tag_clean == 'cteProc':
                    # This IS the CTe content
                    return ET.tostring(elem, encoding='unicode')
                
                # Check for nested cteProc
                cte_proc = elem.find(".//{*}cteProc")
                if cte_proc is not None:
                    return ET.tostring(cte_proc, encoding='unicode')
                
                # Check for text content (escaped XML)
                if elem.text and elem.text.strip():
                    text = elem.text.strip()
                    if text.startswith('<'):
                        return text
                
                # Check nested elements
                for child in elem:
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag == 'cteProc':
                        return ET.tostring(child, encoding='unicode')

        logger.warning("CTe XML not found in response")
        return None

    async def download_cte(self, access_key: str) -> Optional[str]:
        """
        Download CTe XML by access key.
        
        Args:
            access_key: CTe access key (44 digits)
            
        Returns:
            CTe XML string or None if not found
        """
        logger.info(f"Downloading CTe: {access_key}")
        
        try:
            xml = self.build_cte_request_xml(access_key)
            response = await self.send_cte_request(xml)
            cte_xml = self.parse_cte_response(response)
            
            if cte_xml:
                logger.info(f"CTe downloaded successfully: {access_key}")
            else:
                logger.warning(f"CTe not found: {access_key}")
            
            return cte_xml
            
        except Exception as e:
            logger.error(f"CTe download error: {access_key} - {e}")
            return None

    # Legacy method aliases
    def montar_xml_cte(self, chave: str) -> str:
        """Legacy alias for build_cte_request_xml."""
        return self.build_cte_request_xml(chave)

    async def enviar_xml_cte(self, xml: str, max_retries: int = 3) -> str:
        """Legacy alias for send_cte_request."""
        return await self.send_cte_request(xml)

    def parse_xml_cte(self, xml_retorno: str) -> Optional[str]:
        """Legacy alias for parse_cte_response."""
        return self.parse_cte_response(xml_retorno)

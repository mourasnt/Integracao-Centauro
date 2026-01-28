# app/services/vblog/base.py
"""
Base class for VBLOG integration services.
Provides shared HTTP client management, XML building, and retry logic.
"""

import asyncio
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Optional, Any

import httpx

from app.utils.logger import logger


# Common namespace for VBLOG XML
NS = "http://www.controleembarque.com.br"
NSMAP = {"ns": NS}


class VBlogBaseClient(ABC):
    """
    Abstract base class for VBLOG services.
    Provides shared functionality for HTTP requests and XML handling.
    """

    def __init__(
        self,
        cnpj: Optional[str] = None,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.cnpj = cnpj
        self.token = token
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _build_xml_envelope(self, root_tag: str, version: str = "2.00") -> ET.Element:
        """
        Build a base XML envelope with authentication.
        
        Args:
            root_tag: The root element tag name
            version: XML version attribute
            
        Returns:
            ElementTree element with Autentic child
        """
        root = ET.Element(root_tag, {"versao": version, "xmlns": NS})
        
        autentic = ET.SubElement(root, "Autentic")
        ET.SubElement(autentic, "xCNPJ").text = str(self.cnpj) if self.cnpj else ""
        ET.SubElement(autentic, "xToken").text = str(self.token) if self.token else ""
        
        return root

    def _to_xml_string(self, element: ET.Element) -> str:
        """Convert ElementTree element to XML string with declaration."""
        xml_bytes = ET.tostring(element, encoding="utf-8", xml_declaration=True)
        return xml_bytes.decode("utf-8")

    async def _send_with_retry(
        self,
        url: str,
        payload: str | dict,
        content_type: str = "application/xml",
        method: str = "POST",
    ) -> tuple[bool, str, int]:
        """
        Send HTTP request with retry logic.
        
        Args:
            url: Target URL
            payload: XML string or dict for JSON
            content_type: Request content type
            method: HTTP method
            
        Returns:
            Tuple of (success, response_text, status_code)
        """
        client = await self._get_client()
        
        headers = {
            "Content-Type": f"{content_type}; charset=utf-8",
            "Accept": content_type,
        }
        
        attempt = 0
        last_error: Optional[Exception] = None
        
        while attempt < self.max_retries:
            try:
                if content_type == "application/json" and isinstance(payload, dict):
                    resp = await client.request(method, url, json=payload, headers=headers)
                else:
                    content = payload.encode("utf-8") if isinstance(payload, str) else payload
                    resp = await client.request(method, url, content=content, headers=headers)
                
                # Success: 2xx or 3xx
                if resp.status_code < 400:
                    return True, resp.text, resp.status_code
                
                # Client error (4xx): don't retry
                if 400 <= resp.status_code < 500:
                    logger.warning(
                        f"Client error {resp.status_code} for {url}: {resp.text[:200]}"
                    )
                    return False, resp.text, resp.status_code
                
                # Server error (5xx): retry
                last_error = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
                logger.warning(f"Server error {resp.status_code}, attempt {attempt + 1}/{self.max_retries}")
                
            except Exception as e:
                last_error = e
                # Some httpx/httpcore exceptions have empty str() representation
                # (e.g., anyio.EndOfStream, BrokenResourceError)
                error_detail = str(e) if str(e) else f"{type(e).__name__}: args={e.args}"
                logger.warning(
                    f"Network error on attempt {attempt + 1}/{self.max_retries}: "
                    f"{type(e).__name__} - {error_detail}",
                    exc_info=True  # Include full traceback for debugging
                )
            
            attempt += 1
            await asyncio.sleep(0.5 * attempt)  # Exponential backoff
        
        # Build detailed error message for final failure
        if last_error:
            error_msg = str(last_error) if str(last_error) else f"{type(last_error).__name__}: args={last_error.args}"
        else:
            error_msg = "Max retries exceeded"
        logger.error(f"Failed after {self.max_retries} attempts: {error_msg}")
        return False, error_msg, 0

    @staticmethod
    def extract_xml_key(xml_str: str, key_tag: str = "chCTe") -> Optional[str]:
        """
        Extract a key value from CTe/NFe XML.
        
        Args:
            xml_str: The XML content
            key_tag: Tag name to search for (e.g., 'chCTe', 'chNFe')
            
        Returns:
            The key value or None if not found
        """
        try:
            root = ET.fromstring(xml_str)
            ns = {"cte": "http://www.portalfiscal.inf.br/cte"}
            
            # Try with namespace
            elem = root.find(f".//cte:{key_tag}", ns)
            if elem is not None and elem.text:
                return elem.text.strip()
            
            # Try without namespace
            elem = root.find(f".//{key_tag}")
            if elem is not None and elem.text:
                return elem.text.strip()
                
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        except Exception as e:
            logger.error(f"Error extracting key from XML: {e}")
        
        return None

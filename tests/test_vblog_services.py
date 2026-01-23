# tests/test_vblog_services.py
"""
Tests for VBLOG integration services.
Refactored to use async patterns and new English naming.
"""

import pytest
import xml.etree.ElementTree as ET

from app.services.vblog.base import VBlogBaseClient
from app.services.vblog.envdocs import VBlogEnvDocsService
from app.services.vblog.tracking import VBlogTrackingService


class MockVBlogClient(VBlogBaseClient):
    """Mock VBLOG client for testing."""
    
    def __init__(self):
        super().__init__(
            cnpj="12345678901234",
            token="test-token",
            base_url="http://example.local",
        )
    
    async def _get_client(self):
        raise RuntimeError("HTTP not expected in unit tests")


def test_build_envelope():
    """Test XML envelope building."""
    client = MockVBlogClient()
    
    root = client._build_xml_envelope("recepDoc")
    
    # Should be an ElementTree element
    assert root is not None
    assert isinstance(root, ET.Element)
    
    # Should contain authentication - convert to string for parsing
    xml_str = ET.tostring(root, encoding="unicode")
    parsed = ET.fromstring(xml_str)
    
    # Should contain authentication elements
    auth = parsed.find(".//{*}Autentic")
    assert auth is not None


def test_envdocs_build_recep_doc_sub():
    """Test building recepDocSub XML."""
    client = MockVBlogClient()
    svc = VBlogEnvDocsService(client)
    
    inner = '<cteProc xmlns="http://www.portalfiscal.inf.br/cte"><infCte><chCTe>000000000</chCTe></infCte></cteProc>'
    xml = svc.build_recep_doc_sub([inner])
    
    # Should be well-formed XML
    root = ET.fromstring(xml)
    
    # Should contain authentication
    assert root.find(".//{*}xCNPJ") is not None
    assert root.find(".//{*}xToken") is not None
    
    # Should contain cteProc
    found_cte = False
    for elem in root.iter():
        tag = elem.tag
        local = tag.split("}")[-1] if "}" in tag else tag
        if local == "cteProc":
            found_cte = True
            break
    
    assert found_cte, "cteProc not found in xXMLCTe"


def test_envdocs_parse_response_success():
    """Test parsing successful recepDocSub response."""
    client = MockVBlogClient()
    svc = VBlogEnvDocsService(client)
    
    xml_response = '''<?xml version="1.0" encoding="utf-8"?>
    <retrecepDocSub versao="1.00" xmlns="http://www.controleembarque.com.br">
      <Autentic>
        <xCNPJ>12345678901234</xCNPJ>
        <Token>token</Token>
      </Autentic>
      <Control>
        <Cod>001</Cod>
        <xDesc>Sucesso</xDesc>
      </Control>
      <grupoDoc>
        <RetDoc>
          <chDoc>000000000</chDoc>
          <Cod>001</Cod>
          <Desc>OK</Desc>
        </RetDoc>
      </grupoDoc>
    </retrecepDocSub>'''
    
    parsed = svc.parse_response(xml_response)
    
    assert parsed is not None
    # parse_response extracts code and description
    assert "code" in parsed or "Cod" in str(parsed)


def test_envdocs_parse_response_with_garbage():
    """Test parsing response with leading garbage text - should handle gracefully."""
    client = MockVBlogClient()
    svc = VBlogEnvDocsService(client)
    
    garbage = "Some garbage text before xml\n\r"
    xml_response = garbage + '''<?xml version="1.0" encoding="utf-8"?>
    <retrecepDocSub versao="1.00" xmlns="http://www.controleembarque.com.br">
      <Control>
        <Cod>039</Cod>
        <xDesc>Falha no schema XML do CTe</xDesc>
      </Control>
    </retrecepDocSub>'''
    
    # May fail to parse due to garbage, should return raw
    parsed = svc.parse_response(xml_response)
    assert parsed is not None


def test_tracking_build_payload():
    """Test building tracking payload with attachments."""
    svc = VBlogTrackingService(cliente="TEST")
    
    attachments = [{"arquivo": {"nome": "http://example.com/file.pdf", "dados": "ZGVtbw=="}}]
    payload = svc.build_payload(
        document_key="chave1",
        event_code="1",
        attachments=attachments,
    )
    
    assert "documentos" in payload
    doc = payload["documentos"][0]
    assert "anexos" in doc
    assert doc["anexos"] == attachments


def test_tracking_build_payload_without_attachments():
    """Test building tracking payload without attachments."""
    svc = VBlogTrackingService(cliente="TEST")
    
    # Use valid code "1" instead of "2"
    payload = svc.build_payload(
        document_key="chave2",
        event_code="1",
    )
    
    assert "documentos" in payload
    doc = payload["documentos"][0]
    assert doc.get("anexos") is None or doc.get("anexos") == []


@pytest.mark.asyncio
async def test_extract_xml_key():
    """Test extracting CTe key from XML."""
    client = MockVBlogClient()
    
    xml = '''<?xml version="1.0"?>
    <cteProc xmlns="http://www.portalfiscal.inf.br/cte">
        <protCTe>
            <infProt>
                <chCTe>35210512345678901234550010000000011123456789</chCTe>
            </infProt>
        </protCTe>
    </cteProc>'''
    
    key = client.extract_xml_key(xml)
    
    assert key == "35210512345678901234550010000000011123456789"


@pytest.mark.asyncio
async def test_extract_xml_key_not_found():
    """Test extracting key from invalid XML."""
    client = MockVBlogClient()
    
    xml = "<invalid>no key here</invalid>"
    key = client.extract_xml_key(xml)
    
    assert key is None

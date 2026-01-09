import pytest

from app.services.vblog_envdocs_service import VBlogEnvDocsService


class DummyVBlogClient:
    def __init__(self):
        self.base = "http://example.local"
        self.cnpj = "12345678901234"
        self.token = "token"

    async def _get_client(self):
        # Not used in these unit tests
        class Dummy:
            async def post(self, *args, **kwargs):
                raise RuntimeError("HTTP not expected in unit tests")

        return Dummy()


def test_build_recep_doc_sub_single_doc():
    client = DummyVBlogClient()
    svc = VBlogEnvDocsService(client)

    inner = "<cteProc xmlns=\"http://www.controleembarque.com.br\"><infCte><chCTe>000000000</chCTe></infCte></cteProc>"
    xml = svc.build_recep_doc_sub([inner])

    # Deve ser um XML bem formado
    root = ET.fromstring(xml)
    # Verifica a presença de Autentic/xCNPJ e xToken
    assert root.find('.//Autentic/xCNPJ') is not None
    assert root.find('.//Autentic/xToken') is not None
    # Deve conter xXMLCTe/cteProc (mesmo que seja com prefixo de namespace)
    found_cte = False
    for elem in root.iter():
        tag = elem.tag
        local = tag.split('}')[-1] if '}' in tag else tag
        if local == 'cteProc':
            found_cte = True
            # garante que dentro exista chCTe
            assert elem.find('.//{*}chCTe') is not None or elem.find('.//chCTe') is not None
            break
    assert found_cte, 'cteProc não encontrado dentro de xXMLCTe'


def test_parse_retrecep_doc_sub_single_success():
    client = DummyVBlogClient()
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

    parsed = svc.parse_retrecep_doc_sub(xml_response)

    assert parsed is not None
    assert parsed['control']['Cod'] == '001'
    assert parsed['control']['xDesc'] == 'Sucesso'
    assert len(parsed['docs']) == 1
    assert parsed['docs'][0]['chDoc'] == '000000000'
    assert parsed['docs'][0]['Cod'] == '001'
    assert parsed['docs'][0]['Desc'] == 'OK'


def test_parse_retrecep_doc_sub_with_leading_garbage():
    client = DummyVBlogClient()
    svc = VBlogEnvDocsService(client)

    garbage = "Some garbage text before xml\n\r"
    xml_response = garbage + '''<?xml version="1.0" encoding="utf-8"?>
    <retrecepDocSub versao="1.00" xmlns="http://www.controleembarque.com.br">
      <Autentic>
        <xCNPJ>12345678901234</xCNPJ>
        <Token>token</Token>
      </Autentic>
      <Control>
        <Cod>039</Cod>
        <xDesc>Falha no schema XML do CTe</xDesc>
      </Control>
    </retrecepDocSub>'''

    parsed = svc.parse_retrecep_doc_sub(xml_response)

    assert parsed is not None
    assert parsed['control']['Cod'] == '039'
    assert 'Falha no schema' in parsed['control']['xDesc']


def test_parse_retrecep_doc_sub_no_control_or_docs():
    client = DummyVBlogClient()
    svc = VBlogEnvDocsService(client)

    xml_response = '<retrecepDocSub versao="1.00" xmlns="http://www.controleembarque.com.br"><Autentic/></retrecepDocSub>'
    parsed = svc.parse_retrecep_doc_sub(xml_response)

    assert parsed is not None
    assert parsed['control'] == {}
    assert parsed['docs'] == []

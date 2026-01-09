from app.services.vblog_tracking import VBlogTrackingService


def test_montar_payload_includes_anexos():
    svc = VBlogTrackingService()
    anexos = [{"arquivo": {"nome": "http://example.com/file.pdf", "dados": "ZGVtbw=="}}]
    payload = svc.montar_payload(chave_documento="chave1", codigo_evento="1", anexos=anexos)
    assert "documentos" in payload
    doc = payload["documentos"][0]
    assert "anexos" in doc
    assert doc["anexos"] == anexos

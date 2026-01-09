import base64
import uuid
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routes.cargas import router as cargas_router, get_db

from app.services.carga_service import CargaService
from app.services.vblog_tracking import VBlogTrackingService

# create a minimal app for testing that mounts the cargas router
app = FastAPI()
app.include_router(cargas_router)


def test_alterar_status_with_base64_anexo(monkeypatch, tmp_path):
    # auth removed; no override needed

    # prepare dummy carga and cte
    class DummyCTE:
        def __init__(self):
            self.id = uuid.uuid4()
            self.chave = "chave-cte"
            self.nfs = ["nf-1"]
            self.trackings = []

    class DummyCarga:
        def __init__(self):
            self.id = uuid.uuid4()
            self.ctes_cliente = [DummyCTE()]
            self.status = {}

    dummy_carga = DummyCarga()

    monkeypatch.setattr(CargaService, "obter_por_id", lambda db, carga_id: dummy_carga)

    captured = {}

    async def fake_enviar(chave_documento, codigo_evento, data_evento=None, obs=None, tipo="NF", anexos=None):
        captured['args'] = {
            'chave_documento': chave_documento,
            'codigo_evento': codigo_evento,
            'anexos': anexos,
        }
        return True, "ok"

    monkeypatch.setattr(VBlogTrackingService, "enviar", fake_enviar)

    client = TestClient(app)

    b64 = base64.b64encode(b"hello world").decode()

    carga_id = str(uuid.uuid4())
    payload = {"novo_status": {"code": "1"}, "anexos": [{"arquivo": {"dados": b64}}]}

    resp = client.post(f"/cargas/{carga_id}/status", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo_enviado"] == "1"

    # ensure enviar was called and anexos present
    assert 'args' in captured
    assert captured['args']['codigo_evento'] == '1'
    assert captured['args']['anexos'] is not None
    assert len(captured['args']['anexos']) == 1
    anexo = captured['args']['anexos'][0]
    assert 'arquivo' in anexo
    assert 'nome' in anexo['arquivo']
    assert 'dados' in anexo['arquivo']
    # dados should be same base64
    assert anexo['arquivo']['dados'] == b64

    # cleanup override
    app.dependency_overrides.clear()


def test_alterar_status_with_file_upload(monkeypatch, tmp_path):
    import pytest
    import app.routes.cargas as cargas_routes
    if not getattr(cargas_routes, 'HAS_MULTIPART', False):
        pytest.skip('python-multipart not installed: skipping multipart test')

    # auth removed; no override needed

    # prepare dummy carga and cte
    class DummyCTE:
        def __init__(self):
            self.id = uuid.uuid4()
            self.chave = "chave-cte"
            self.nfs = ["nf-1"]
            self.trackings = []

    class DummyCarga:
        def __init__(self):
            self.id = uuid.uuid4()
            self.ctes_cliente = [DummyCTE()]
            self.status = {}

    dummy_carga = DummyCarga()

    monkeypatch.setattr(CargaService, "obter_por_id", lambda db, carga_id: dummy_carga)

    captured = {}

    async def fake_enviar(chave_documento, codigo_evento, data_evento=None, obs=None, tipo="NF", anexos=None):
        captured['args'] = {
            'chave_documento': chave_documento,
            'codigo_evento': codigo_evento,
            'anexos': anexos,
        }
        return True, "ok"

    monkeypatch.setattr(VBlogTrackingService, "enviar", fake_enviar)

    client = TestClient(app)

    carga_id = str(uuid.uuid4())

    # create a small file
    files = {
        'files': ('test.txt', b'hello file', 'text/plain')
    }

    # send multipart form-data; novo_status in form as JSON string
    data = {
        'novo_status_json': '{"code": "1"}'
    }

    resp = client.post(f"/cargas/{carga_id}/status", data=data, files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo_enviado"] == "1"

    # ensure enviar was called and anexos present
    assert 'args' in captured
    assert captured['args']['codigo_evento'] == '1'
    assert captured['args']['anexos'] is not None
    assert len(captured['args']['anexos']) == 1
    anexo = captured['args']['anexos'][0]
    assert 'arquivo' in anexo
    assert 'nome' in anexo['arquivo']
    assert 'dados' in anexo['arquivo']

    # cleanup override
    app.dependency_overrides.clear()
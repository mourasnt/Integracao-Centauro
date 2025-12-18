# vblog_transito.py
from typing import List, Optional, Any
from pydantic import BaseModel, Field
import httpx # type: ignore
import xml.etree.ElementTree as ET
import asyncio

NS = "http://www.controleembarque.com.br"
NSMAP = {"ns": NS}


# -----------------------
# Modelos Pydantic
# -----------------------
class Documento(BaseModel):
    tipo: Optional[str] = None  # 'chaveCTe' or 'xml' or others
    valor: Optional[str] = None  # texto entre tags (chave) ou None for empty element
    xDocFim: Optional[str] = None
    tpOp: Optional[str] = None
    other_attribs: dict = Field(default_factory=dict)


class Motorista(BaseModel):
    cpf: Optional[str] = None
    nome: Optional[str] = None
    other: dict = Field(default_factory=dict)


class Veiculo(BaseModel):
    tracao: Optional[str] = None
    reboque: Optional[str] = None
    other: dict = Field(default_factory=dict)


class ModalRodoviario(BaseModel):
    motorista: Optional[Motorista] = None
    veiculo: Optional[Veiculo] = None
    other: dict = Field(default_factory=dict)


class ControleTransitoModel(BaseModel):
    xDocTransp: Optional[str] = None
    docs: List[Documento] = Field(default_factory=list)
    modal_rodoviario: Optional[ModalRodoviario] = None
    other: dict = Field(default_factory=dict)


class RetornoControleTransito(BaseModel):
    codigo: Optional[int] = None
    descricao: Optional[str] = None
    protocolo: Optional[str] = None
    transitos: List[ControleTransitoModel] = Field(default_factory=list)
    raw_xml: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


# -----------------------
# Service
# -----------------------
class VBlogTransitoService:
    def __init__(
        self,
        cnpj: str,
        token: str,
        ambiente_base: str = "http://homolog.controleembarque.com.br",
        timeout_seconds: float = 10.0,
    ):
        self.cnpj = cnpj
        self.token = token
        self.base = ambiente_base.rstrip("/")
        self.endpoint = f"{self.base}/Webapi/transito/aberto/v2"
        self.timeout = timeout_seconds
        # httpx client should be created per event loop or reused carefully
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def montar_xml(self, tpRet: int = 7, stTransito: int = 1) -> str:
        """
        Monta o XML de envio conforme o XSD/envio do manual.
        """
        env = ET.Element("envDocSubTransito", {"versao": "2.00", "xmlns": NS})
        autentic = ET.SubElement(env, "Autentic")
        ET.SubElement(autentic, "xCNPJ").text = str(self.cnpj)
        # Nota: no XSD original token é <Token> mas no seu exemplo de envio usa xToken/xToken? manter xToken conforme seu exemplo
        # Aqui colocamos xToken se informado
        ET.SubElement(autentic, "xToken").text = str(self.token)

        control = ET.SubElement(env, "Control")
        ET.SubElement(control, "tpRet").text = str(tpRet)
        ET.SubElement(control, "stTransito").text = str(stTransito)

        xml_bytes = ET.tostring(env, encoding="utf-8", xml_declaration=True)
        return xml_bytes.decode("utf-8")

    async def enviar_xml(self, xml: str, max_retries: int = 3) -> str:
        """
        Envia o XML para o endpoint e retorna o XML de resposta como string.
        Faz retries simples em caso de falha de rede ou 5xx.
        """
        attempt = 0
        last_exc: Optional[Exception] = None
        client = await self._get_client()

        headers = {
            "Content-Type": "application/xml; charset=utf-8",
            "Accept": "application/xml",
        }

        while attempt < max_retries:
            try:
                resp = await client.post(self.endpoint, content=xml.encode("utf-8"), headers=headers)
                # resposta 200..399 é considerada válida
                if resp.status_code < 400:
                    return resp.text
                # para 4xx, não retry (provavelmente erro do pedido), devolve conteúdo para análise
                if 400 <= resp.status_code < 500:
                    return resp.text
                # 5xx -> retry
                last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            except (httpx.RequestError, httpx.NetworkError) as e:
                last_exc = e
            attempt += 1
            await asyncio.sleep(0.5 * attempt)  # backoff simples

        raise last_exc or RuntimeError("Falha desconhecida ao enviar requisição")

    def _safe_find_text(self, root: ET.Element, path: str) -> Optional[str]:
        el = root.find(path, NSMAP)
        return None if el is None else (el.text.strip() if el.text is not None else None)

    def parse_resposta(self, xml_text: str) -> RetornoControleTransito:
        """
        Faz parse do XML retornado pela API e transforma em modelos Pydantic.
        Modo resiliente: campos ausentes resultam em None / listas vazias.
        """
        result = RetornoControleTransito(raw_xml=xml_text)

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            result.warnings.append(f"XML inválido: {e}")
            return result

        # Código e descrição (Control)
        cod_text = self._safe_find_text(root, ".//ns:Control/ns:Cod")
        try:
            result.codigo = int(cod_text) if cod_text is not None and cod_text.isdigit() else None
        except Exception:
            result.codigo = None

        result.descricao = self._safe_find_text(root, ".//ns:Control/ns:xDesc")
        result.protocolo = self._safe_find_text(root, ".//ns:nProt")

        # Se Cod == 13 -> nenhum documento (não é erro)
        if result.codigo == 13:
            result.warnings.append("Código 13 - Nenhum documento encontrado")

        # Encontrar todos ControleTransito
        controle_nodes = root.findall(".//ns:ControleTransito", NSMAP)
        for ct_node in controle_nodes:
            ct_model = ControleTransitoModel()
            ct_model.xDocTransp = ct_node.attrib.get("xDocTransp")

            # Docs dentro de cada ControleTransito: podem existir vários <Docs>
            docs_nodes = ct_node.findall(".//ns:Docs", NSMAP)
            for docs_node in docs_nodes:
                # Cada <Docs> contém elementos filhos que podem ser <xml> ou <chaveCTe>
                for child in list(docs_node):
                    # obtém localname sem namespace
                    tag = child.tag
                    if "}" in tag:
                        local = tag.split("}", 1)[1]
                    else:
                        local = tag
                    doc = Documento(tipo=local, valor=(child.text.strip() if child.text else None))
                    # captura atributos se existirem
                    doc.xDocFim = child.attrib.get("xDocFim")
                    doc.tpOp = child.attrib.get("tpOp")
                    # other attributes
                    doc.other_attribs = {k: v for k, v in child.attrib.items() if k not in ("xDocFim", "tpOp")}
                    ct_model.docs.append(doc)

                # também captura atributos do próprio <Docs> (ex: cUFIni, cMunIni, xDocIni, cUFFim, cMunFim)
                ct_model.other.update(docs_node.attrib)

            # modal rodoviario (opcional)
            modal_node = ct_node.find(".//ns:infModalRodoviario", NSMAP)
            if modal_node is not None:
                modal = ModalRodoviario()
                # Motorista -> pode aparecer em Moto/Principal/CPFmotorista ou CPFmotorista direto
                cpf_node = modal_node.find(".//ns:CPFmotorista", NSMAP)
                name_node = modal_node.find(".//ns:NomeMotorista", NSMAP)  # hypothetical
                motorista = Motorista()
                if cpf_node is not None and cpf_node.text:
                    motorista.cpf = cpf_node.text.strip()
                if name_node is not None and name_node.text:
                    motorista.nome = name_node.text.strip()
                # other motorista fields capture
                modal.motorista = motorista

                # Veiculo
                veic = Veiculo()
                tracao_node = modal_node.find(".//ns:Tracao", NSMAP)
                reboque_node = modal_node.find(".//ns:Reboque", NSMAP)
                if tracao_node is not None and tracao_node.text:
                    veic.tracao = tracao_node.text.strip()
                if reboque_node is not None and reboque_node.text:
                    veic.reboque = reboque_node.text.strip()
                modal.veiculo = veic

                # any other modal attributes/texts
                modal.other = {c.tag.split("}", 1)[1] if "}" in c.tag else c.tag: (c.text.strip() if c.text else None)
                               for c in list(modal_node) if (c.text and c.text.strip())}
                ct_model.modal_rodoviario = modal

            # caso existam outros atributos no ControleTransito
            ct_model.other.update(ct_node.attrib)
            result.transitos.append(ct_model)

        return result

    async def consultar_transito_aberto(self, tpRet: int = 7, stTransito: int = 1) -> RetornoControleTransito:
        """
        Método principal que monta o XML, envia e parseia o retorno.
        Resiliente: sempre devolve um RetornoControleTransito (mesmo em erro de parse).
        """
        xml = self.montar_xml(tpRet=tpRet, stTransito=stTransito)
        try:
            resposta = await self.enviar_xml(xml)
        except Exception as e:
            ret = RetornoControleTransito(raw_xml=None)
            ret.warnings.append(f"Falha no envio: {e}")
            return ret

        parsed = self.parse_resposta(resposta)
        return parsed

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# -----------------------
# Exemplo de uso com FastAPI
# -----------------------
# Em seu arquivo FastAPI (por exemplo main.py ou router), use algo assim:

"""
from fastapi import FastAPI, Depends
from vblog_transito import VBlogTransitoService, RetornoControleTransito

app = FastAPI()

# crie um factory/dep para o service
def get_transito_service() -> VBlogTransitoService:
    # preferível carregar cnpj/token de variáveis de ambiente
    return VBlogTransitoService(cnpj="34790798000134", token="t2SNUKi7pt6D9pbEoJVC")

@app.get("/transitos-abertos", response_model=RetornoControleTransito)
async def transitos_abertos(service: VBlogTransitoService = Depends(get_transito_service)):
    result = await service.consultar_transito_aberto()
    # se desejar, transforme warnings em status code ou log
    return result
"""

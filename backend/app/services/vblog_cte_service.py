# app/services/vblog_cte_service.py

import httpx
import asyncio
import xml.etree.ElementTree as ET

from typing import Optional


NS = "http://www.controleembarque.com.br"
NSMAP = {"ns": NS}


class VBlogCTeService:
    """
    Serviço para consultar CT-es individuais no endpoint:
    /Webapi/transito/cte
    """

    def __init__(self, vblog_client):
        """
        Recebe o mesmo VBlogTransitoService (compartilha token, CNPJ, cliente http).
        """
        self.vblog = vblog_client
        self.endpoint = f"{self.vblog.base}/Webapi/transito/cte"

    # ------------------------------------
    # 1) Montar XML de envio
    # ------------------------------------
    def montar_xml_cte(self, chave: str) -> str:
        """
        XML de requisição para baixar CT-e completo por chave.
        """
        env = ET.Element("envCteTransito", {"versao": "2.00", "xmlns": NS})

        autentic = ET.SubElement(env, "Autentic")
        ET.SubElement(autentic, "xCNPJ").text = str(self.vblog.cnpj)
        ET.SubElement(autentic, "xToken").text = str(self.vblog.token)

        doc = ET.SubElement(env, "Doc")
        ET.SubElement(doc, "chaveCTe").text = chave

        xml_bytes = ET.tostring(env, encoding="utf-8", xml_declaration=True)
        return xml_bytes.decode("utf-8")

    # ------------------------------------
    # 2) Enviar requisição com retry
    # ------------------------------------
    async def enviar_xml_cte(self, xml: str, max_retries: int = 3) -> str:
        client = await self.vblog._get_client()

        headers = {
            "Content-Type": "application/xml; charset=utf-8",
            "Accept": "application/xml",
        }

        attempt = 0
        last_exc = None

        while attempt < max_retries:
            try:
                resp = await client.post(
                    self.endpoint,
                    content=xml.encode("utf-8"),
                    headers=headers,
                )

                if resp.status_code < 400:
                    return resp.text

                if 400 <= resp.status_code < 500:
                    return resp.text

                last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

            except (httpx.RequestError, httpx.NetworkError) as e:
                last_exc = e

            attempt += 1
            await asyncio.sleep(0.4 * attempt)

        raise last_exc or RuntimeError("Falha ao consultar CT-e")

    # ------------------------------------
    # 3) Parsear o retorno e extrair XML do CT-e
    # ------------------------------------
    def parse_xml_cte(self, xml_retorno: str) -> Optional[str]:
        """
        Extrai o XML real do CT-e retornado pela VBLOG.
        Normalmente vem dentro de:
        <Docs>
           <xml xDocFim="..." tpOp="..."> ...xml do CTe... </xml>
        </Docs>
        """
        try:
            root = ET.fromstring(xml_retorno)
        except ET.ParseError:
            return None

        xml_nodes = root.findall(".//ns:xml", NSMAP)

        # Caso tenham vários, retornamos o primeiro
        for node in xml_nodes:
            if node.text:
                return node.text.strip()

        return None

    # ------------------------------------
    # 4) Fluxo completo — baixar CT-e
    # ------------------------------------
    async def baixar_cte(self, chave: str) -> Optional[str]:
        """
        - Monta XML de solicitação
        - Envia para API VBLOG
        - Extrai o XML real do CT-e
        - Retorna o XML bruto para salvar no banco
        """
        xml_envio = self.montar_xml_cte(chave)
        xml_retorno = await self.enviar_xml_cte(xml_envio)

        xml_cte = self.parse_xml_cte(xml_retorno)

        return xml_cte

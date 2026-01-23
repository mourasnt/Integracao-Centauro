import httpx
import asyncio
import xml.etree.ElementTree as ET

from typing import Optional


NS = "http://www.controleembarque.com.br"
# NSMAP removido pois a montagem agora é manual e limpa


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
        # Endpoint v2 costuma ser o correto para envDocSubTransitoCTe
        self.endpoint = f"{self.vblog.base}/Webapi/transito/cte/v2"

    # ------------------------------------
    # 1) Montar XML de envio (MANUAL / F-STRING)
    # ------------------------------------
    def montar_xml_cte(self, chave: str) -> str:
        """
        XML de requisição para baixar CT-e completo por chave.
        IMPORTANTE: Construído manualmente via f-string para garantir que não
        haja repetição de namespaces (xmlns) nas tags filhas.
        """
        return (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<envDocSubTransitoCTe versao="2.00" xmlns="{NS}">'
            f'<Autentic>'
            f'<xCNPJ>{self.vblog.cnpj}</xCNPJ>'
            f'<xToken>{self.vblog.token}</xToken>'
            f'</Autentic>'
            f'<Control>'
            f'<tpRet>'
            f'3'
            f'</tpRet>'
            f'<Docs>'
            f'<chaveCTe>{chave}</chaveCTe>'
            f'</Docs>'
            f'</Control>'
            f'</envDocSubTransitoCTe>'
        )

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

        # print(xml) # Debug XML envio
        while attempt < max_retries:
            try:
                # print(f"[DEBUG] XML Envio: {xml}") # Descomente para debugar o envio
                resp = await client.post(
                    self.endpoint,
                    content=xml.encode("utf-8"),
                    headers=headers,
                    timeout=30.0,  # Timeout mais longo para downloads
                )

                if resp.status_code < 400:
                    return resp.text

                # Log de erro HTTP
                print(f"[VBLOG] Erro HTTP {resp.status_code} ao baixar CTe: {resp.text[:200]}")

                if 400 <= resp.status_code < 500:
                    # Erros 4xx (Client Error) não adiantam tentar de novo
                    return resp.text

                last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

            except (httpx.RequestError, httpx.NetworkError) as e:
                last_exc = e

            attempt += 1
            await asyncio.sleep(1 * attempt)

        print(f"[VBLOG] Falha final ao baixar CTe após retries. Erro: {last_exc}")
        raise last_exc or RuntimeError("Falha ao consultar CT-e")

    # ------------------------------------
    # 3) Parsear o retorno e extrair XML do CT-e
    # ------------------------------------
    def parse_xml_cte(self, xml_retorno: str) -> Optional[str]:
        """
        Extrai o XML real do CT-e retornado pela VBLOG.
        Tenta ser robusto contra namespaces e formatos de retorno (escapado ou aninhado).
        """
        if not xml_retorno:
            return None

        try:
            # Remove declaração de encoding se existir para evitar conflitos no parser
            if xml_retorno.startswith("<?xml") and "encoding" in xml_retorno:
                pass 

            root = ET.fromstring(xml_retorno)
            # print(xml_retorno) # Debug retorno
        except ET.ParseError as e:
            print(f"[VBLOG] Erro de Parse no XML de retorno: {e}")
            return None

        # --- Verificação de Erro Lógico da API (Tag Control/xDesc) ---
        # Procura por mensagens de erro dentro do XML válido
        for elem in root.iter():
            if "Control" in elem.tag:
                # Busca Cod e xDesc ignorando namespace
                cod = elem.find(f".//{{*}}Cod") or elem.find("Cod")
                desc = elem.find(f".//{{*}}xDesc") or elem.find("xDesc")
                compl = elem.find(f".//{{*}}xCompl") or elem.find("xCompl")

                # Cod '001' geralmente é sucesso. Outros são erro.
                if cod is not None and cod.text not in ["001", "1"]: 
                    msg = getattr(desc, 'text', 'Sem descrição')
                    detalhe = getattr(compl, 'text', '')
                    print(f"[VBLOG] API retornou Erro Lógico: {msg} | Detalhe: {detalhe}")
                    # Não retornamos None aqui para deixar o código tentar achar a tag de XML
                    # caso o erro seja parcial, mas geralmente isso indica falha.

        # --- Busca da tag com o XML (xXMLCTe ou xml) ---
        # No log enviado: <xXMLCTe><cteProc ...></cteProc></xXMLCTe>
        xml_node = None
        
        # Lista de tags possíveis onde o XML do CTe pode estar
        possible_tags = ['xXMLCTe', 'xml', 'cteProc']

        for elem in root.iter():
            # Limpa o namespace para comparar apenas o nome da tag
            tag_clean = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if tag_clean in possible_tags:
                xml_node = elem
                break
        
        if xml_node is None:
            # Se não achou <xXMLCTe> ou <xml>, loga para debug
            print(f"[VBLOG] Tags {possible_tags} não encontradas no retorno.")
            return None

        # CENÁRIO A: O conteúdo é texto escapado (Ex: &lt;CTe...)
        if xml_node.text and len(xml_node.text.strip()) > 10:
            return xml_node.text.strip()
        
        # CENÁRIO B: O conteúdo foi parseado como elementos filhos 
        # Ex: <xXMLCTe><cteProc>...</cteProc></xXMLCTe>
        children = list(xml_node)
        if children:
            try:
                # Pega o primeiro filho (deve ser cteProc ou CTe)
                # 'encoding="unicode"' retorna string ao invés de bytes
                cte_content = ET.tostring(children[0], encoding="unicode")
                return cte_content
            except Exception as e:
                print(f"[VBLOG] Erro ao serializar filho da tag <{xml_node.tag}>: {e}")
                return None

        # CENÁRIO C: A própria tag encontrada já é o XML (ex: se achou cteProc direto)
        # O iter() pode ter achado o cteProc dentro do xXMLCTe
        if 'cteProc' in xml_node.tag:
             try:
                return ET.tostring(xml_node, encoding="unicode")
             except:
                 pass

        print(f"[VBLOG] Tag <{xml_node.tag}> encontrada mas vazia (sem texto e sem filhos úteis).")
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
        try:
            xml_retorno = await self.enviar_xml_cte(xml_envio)
            
            if not xml_retorno:
                return None

            xml_cte = self.parse_xml_cte(xml_retorno)
            return xml_cte
            
        except Exception as e:
            print(f"[VBLOG] Exceção ao baixar CTe {chave}: {e}")
            return None
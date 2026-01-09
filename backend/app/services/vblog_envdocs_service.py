import json
import httpx
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
import re

NS_URI = "http://www.controleembarque.com.br"
# Namespaces auxiliares não são mais usados no parse/rebuild, pois injetaremos o XML pronto
# Mantidos apenas se necessário para alguma validação futura

class VBlogEnvDocsService:

    def __init__(self, vblog_client):
        self.vblog = vblog_client
        self.endpoint = f"{self.vblog.base}/Webapi/envDocs/Upload/CTe"

    def _tag(self, tag: str) -> str:
        """Helper para adicionar o namespace VBLOG nas tags"""
        return f"{{{NS_URI}}}{tag}"

    def _strip_namespace(self, elem: ET.Element) -> ET.Element:
        """
        Remove namespace do elemento e de todos os filhos (Recursive)
        """
        tag = elem.tag.split('}')[-1]
        new_elem = ET.Element(tag, elem.attrib)
        new_elem.text = elem.text
        new_elem.tail = elem.tail
        for child in list(elem):
            new_elem.append(self._strip_namespace(child))
        return new_elem

    # ------------------------------------------------
    # MONTA XML DE ENVIO (ESTRATÉGIA DE INJEÇÃO DIRETA)
    # ------------------------------------------------
    def build_recep_doc_sub(self, xml_ctes: List[str]) -> str:
        """
        Gera o envelope VBlog e injeta o XML do CT-e diretamente como string.
        Isso preserva 100% da estrutura, namespaces, CDATA e Assinatura do original.
        """

        # 1. Configura namespace do Envelope
        ET._namespace_map = {} 
        ET.register_namespace('', NS_URI) # Default VBLOG

        # 2. Estrutura do Envelope VBLOG
        env = ET.Element(self._tag("recepDocSub"), {"versao": "1.00"})

        # Autentic
        autentic = ET.SubElement(env, self._tag("Autentic"))
        ET.SubElement(autentic, self._tag("xCNPJ")).text = re.sub(r'\D', '', str(self.vblog.cnpj))
        ET.SubElement(autentic, self._tag("xToken")).text = str(self.vblog.token)

        # Control
        control = ET.SubElement(env, self._tag("Control"))

        # Dicionário para guardar o XML limpo que será injetado depois
        payloads_map = {}

        for idx, raw_cte in enumerate(xml_ctes):
            grupo = ET.SubElement(control, self._tag("grupoDoc"))
            xxml = ET.SubElement(grupo, self._tag("xXMLCTe"))

            # Criamos um TOKEN único para substituir depois
            token_placeholder = f"___PAYLOAD_CTE_{idx}___"
            xxml.text = token_placeholder

            # Limpa apenas o cabeçalho <?xml ... ?> e espaços extras das pontas
            # O conteúdo interno (cteProc) é preservado intacto
            clean_xml = self._clean_cte_string(raw_cte)
            payloads_map[token_placeholder] = clean_xml

        # 3. Gera string do Envelope (o ElementTree vai escapar os tokens, ex: &lt;___PAYLOAD...&gt;)
        # Mas como usamos tokens alfanuméricos simples, eles não sofrem escape.
        xml_str = ET.tostring(env, encoding="utf-8").decode("utf-8")

        # 4. Ajuste do Namespace na Raiz (Garante que esteja limpo)
        xml_str = re.sub(r'<recepDocSub[^>]*>', f'<recepDocSub versao="1.00" xmlns="{NS_URI}">', xml_str, count=1)

        # 5. INJEÇÃO DOS PAYLOADS (Substitui os tokens pelo XML real)
        for token, raw_content in payloads_map.items():
            xml_str = xml_str.replace(token, raw_content)

        return xml_str

    # ------------------------------------------------
    # LIMPEZA ESTRUTURAL DO XML DE ENTRADA
    # ------------------------------------------------
    def _clean_cte_string(self, raw: str) -> str:
        if not raw: return ""
        s = str(raw).strip()
        
        # Remove caracteres de escape de JSON/String literals se vierem "sujos"
        s = s.replace('\\"', '"')  # \" -> "
        s = s.replace('\\n', '')   # \n literal -> vazio
        s = s.replace('\\r', '')   # \r literal -> vazio
        s = s.replace('\\t', '')   # \t literal -> vazio
        
        # CUIDADO: Não remover \n reais se quiser manter a formatação bonita ("pretty print")
        # Se o servidor aceitar XML em uma linha, descomente as linhas abaixo:
        # s = s.replace('\n', '')
        # s = s.replace('\r', '')
        
        # Remove barras invertidas soltas
        s = s.replace('\\', '') 

        # Remove espaços extras entre atributos (ex: versao= "4.00" -> versao="4.00")
        s = re.sub(r'=\s+"', '="', s)

        # Remove cabeçalho XML (<?xml ... ?>) pois ele será injetado dentro de outro XML
        if s.startswith("<?xml"):
            idx = s.find("?>")
            if idx != -1:
                s = s[idx + 2:].strip()

        return s

    # ------------------------------------------------
    # ENVIO HTTP POST
    # ------------------------------------------------
    async def post_recep_doc_sub(self, xml: str, max_retries: int = 3) -> str:
        client = await self.vblog._get_client()
        headers = {"Content-Type": "application/xml; charset=utf-8"}

        for attempt in range(max_retries):
            try:
                resp = await client.post(
                    self.endpoint,
                    content=xml.encode("utf-8"),
                    headers=headers,
                    timeout=30,
                )
                if resp.status_code < 500:
                    return resp.text
            except httpx.RequestError:
                await asyncio.sleep(attempt + 1)

        raise RuntimeError("Falha ao enviar recepDocSub")

    # ------------------------------------------------
    # PARSER DO RETORNO
    # ------------------------------------------------
    def parse_retrecep_doc_sub(self, xml_retorno: str) -> Optional[dict]:
        if not xml_retorno:
            return None

        # 1. Tenta detectar se é JSON
        try:
            retorno_json = json.loads(xml_retorno)
            # Estrutura padrão que você usa:
            r = retorno_json.get("retrecepDocSub", {})
            parsed = {
                "control": r.get("Control", {}),
                "docs": [],
            }

            # Retorna lista de docs
            grupo = r.get("grupoDoc")
            if grupo:
                # Pode ser um dict único ou lista
                if isinstance(grupo, list):
                    for g in grupo:
                        rd = g.get("RetDoc")
                        if rd:
                            parsed["docs"].append(rd)
                elif isinstance(grupo, dict):
                    rd = grupo.get("RetDoc")
                    if rd:
                        parsed["docs"].append(rd)

            return parsed

        except json.JSONDecodeError:
            # Não é JSON, tenta XML normal
            try:
                xml_text = xml_retorno.replace('\ufeff', '').strip()
                root = ET.fromstring(xml_text)
            except Exception:
                return None

            # Extrai control/docs do XML (se precisar manter compatibilidade)
            result = {"control": {}, "docs": []}
            def clean_tag(t): return t.split('}')[-1] if '}' in t else t
            for elem in root.iter():
                tag_name = clean_tag(elem.tag)
                if tag_name == "Control":
                    for child in elem:
                        result["control"][clean_tag(child.tag)] = child.text or ''
                elif tag_name == "RetDoc":
                    doc = {"chDoc": '', "Cod": '', "Desc": ''}
                    for child in elem:
                        doc[clean_tag(child.tag)] = child.text or ''
                    result["docs"].append(doc)
            return result

    async def enviar_ctes_and_parse(self, xml_ctes: List[str]) -> Dict:
        """
        Envia os CT-es para o VBLOG e retorna em formato padrão:
        {
            "status": int,
            "erro": bool,
            "mensagem": str,
            "docs": [...],
            "raw": str
        }
        """
        xml_envio = self.build_recep_doc_sub(xml_ctes)
        
        # Inicializa retorno padrão
        retorno_padrao = {
            "status": 500,
            "erro": True,
            "mensagem": "Erro desconhecido",
            "docs": [],
            "raw": None
        }

        try:
            retorno = await self.post_recep_doc_sub(xml_envio)
            retorno_padrao["raw"] = retorno

        except Exception as e:
            retorno_padrao["mensagem"] = f"Falha ao enviar XML: {e}"
            return retorno_padrao

        # ----------- PARSE DE JSON OU XML ----------- #
        parsed = self.parse_retrecep_doc_sub(retorno)

        if not parsed:
            retorno_padrao["mensagem"] = "Não foi possível interpretar o retorno do VBLOG"
            retorno_padrao["status"] = 400
            return retorno_padrao

        # ----------- NORMALIZA STATUS E MENSAGEM ----------- #
        # Se houver Control com código
        control = parsed.get("control", {})
        cod = control.get("Cod") or control.get("cod") or ""
        xdesc = control.get("xDesc") or control.get("xdesc") or ""

        # Mensagem final
        if cod in ("001", "100"):  # Ajuste conforme VBLOG define "sucesso"
            retorno_padrao["erro"] = False
            retorno_padrao["status"] = 200
            retorno_padrao["mensagem"] = xdesc or "Processado com sucesso"
        else:
            retorno_padrao["erro"] = True
            retorno_padrao["status"] = 400
            # Se houver docs com erro, concatena
            if parsed.get("docs"):
                mensagens_docs = "; ".join([f"{d.get('chDoc','')}: {d.get('Desc','')}" for d in parsed["docs"]])
                retorno_padrao["mensagem"] = mensagens_docs
            else:
                retorno_padrao["mensagem"] = xdesc or "Erro no processamento"

        retorno_padrao["docs"] = parsed.get("docs", [])

        return retorno_padrao
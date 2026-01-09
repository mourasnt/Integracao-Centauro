from typing import Optional
from sqlalchemy.orm import Session

from app.services.carga_service import CargaService
from app.services.cte_cliente_service import CTeClienteService
from app.models.carga import Carga
from app.schemas.carga import CargaCreate

from app.schemas.cte_cliente import CTeClienteCreate
from app.services.localidades_service import LocalidadesService

import xml.etree.ElementTree as ET

from app.services.vblog_transito import (
    VBlogTransitoService,
    RetornoControleTransito,
)

class TransitoIntegrationService:

    def __init__(self, vblog: VBlogTransitoService):
        """
        Este serviço integra:
        - VBLOG (consulta trânsitos / CT-es)
        - Banco de dados (Cargas, CTeCliente)
        """
        self.vblog = vblog

    # -------------------------------------------
    # Verifica se já existe carga pelo xDocTransp
    # -------------------------------------------
    @staticmethod
    def obter_carga_por_doc(db: Session, xDocTransp: str) -> Optional[Carga]:
        return (
            db.query(Carga)
            .filter(Carga.id_cliente == xDocTransp)  # usamos id_cliente para identificar VBLOG
            .first()
        )

    # -------------------------------------------
    # 1) Sincronizar trânsitos abertos
    # -------------------------------------------
    async def sincronizar_transitos_abertos(self, db: Session):
        resposta: RetornoControleTransito = await self.vblog.consultar_transito_aberto()

        if resposta.codigo is None:
            print("Erro ao consultar trânsitos abertos na VBLOG")
            return []

        cargas_criadas = []

        for transito in resposta.transitos:
            xDocTransp = transito.xDocTransp
            if not xDocTransp:
                continue

            # Verifica se já existe carga no banco
            carga = self.obter_carga_por_doc(db, xDocTransp)

            if not carga:

                # Se por acaso transito.other for None, usamos dicionário vazio para não quebrar
                other_data = getattr(transito, 'other', {}) or {}
                
                cod_uf_ini = other_data.get("cUFIni")
                cod_mun_ini = other_data.get("cMunIni")
                cod_uf_fim = other_data.get("cUFFim")
                cod_mun_fim = other_data.get("cMunFim")

                # 2. Buscar objetos no banco de dados (SQLAlchemy Objects)
                obj_uf_ini = LocalidadesService.get_estado_por_codigo(db, cod_uf_ini)
                obj_mun_ini = LocalidadesService.get_municipio_por_codigo(db, cod_mun_ini)
                obj_uf_fim = LocalidadesService.get_estado_por_codigo(db, cod_uf_fim)
                obj_mun_fim = LocalidadesService.get_municipio_por_codigo(db, cod_mun_fim)

                # 3. Montar dicionários extraindo apenas a STRING (.sigla ou .nome)
                # Isso resolve o erro "Input should be a valid string" do Pydantic
                origem_uf = {
                    "cod": cod_uf_ini,
                    "uf": obj_uf_ini.sigla if obj_uf_ini else None 
                }
                origem_municipio = {
                    "cod": cod_mun_ini,
                    "municipio": obj_mun_ini.nome if obj_mun_ini else None
                }
                destino_uf = {
                    "cod": cod_uf_fim,
                    "uf": obj_uf_fim.sigla if obj_uf_fim else None
                }
                destino_municipio = {
                    "cod": cod_mun_fim,
                    "municipio": obj_mun_fim.nome if obj_mun_fim else None
                }
                
                # 4. Criar a carga
                carga = CargaService.criar_carga(
                    db,
                    CargaCreate(
                        id_cliente=xDocTransp,
                        origem_uf=origem_uf,
                        origem_municipio=origem_municipio,
                        destino_uf=destino_uf,
                        destino_municipio=destino_municipio,
                    ),
                )
                
                # Commit inicial para salvar a Carga antes de vincular CT-es
                db.commit()

            # Registrar CT-es
            novos_ctes = False
            
            # Garante que docs seja iterável
            docs_list = transito.docs if transito.docs else []
            
            for doc in docs_list:
                # Verifica o tipo e valor antes de prosseguir
                tipo = getattr(doc, 'tipo', None)
                valor = getattr(doc, 'valor', None)

                if tipo == "chaveCTe" and valor:
                    chave = valor.strip()
                    
                    # Verifica duplicidade
                    existe = (
                        db.query(Carga)
                        .join(Carga.ctes_cliente)
                        .filter(Carga.id == carga.id)
                        .filter(Carga.ctes_cliente.any(chave=chave))
                        .first()
                    )

                    if not existe:
                        CTeClienteService.adicionar_cte(
                            db,
                            carga_id=carga.id,
                            data=CTeClienteCreate(chave=chave, xml=None),
                        )
                        novos_ctes = True
            
            if novos_ctes:
                db.commit()

            # ==========================================================
            # CORREÇÃO 2: Baixar XML e Atualizar Objeto
            # ==========================================================
            try:
                # 1. Garante que a variável 'carga' veja os novos CTes inseridos
                db.refresh(carga) 
                
                # 2. Baixa e salva os XMLs no banco
                await self.baixar_ctes_da_carga(db, carga)
                
                # 3. Força o SQLAlchemy a recarregar os dados do banco na próxima leitura
                # Isso garante que quando 'carga' for serializada no return, ela tenha os XMLs
                db.expire(carga) 
                db.refresh(carga)
                
            except Exception as e:
                print(f"Aviso: Erro no fluxo de download de XML para carga {carga.id_cliente}: {e}")

            # Adiciona na lista de retorno
            cargas_criadas.append(carga)

            # 3 - Extrair nfs do xml de cada cte
            for cte in carga.ctes_cliente:
                if cte.xml_encrypted:
                    try:
                        nfs = await self.extrair_nfs_cte(cte.xml)
                        cte.nfs = nfs
                        db.add(cte)
                    except Exception as e:
                        print(f"Aviso: Erro ao extrair NFs do CT-e {cte.chave}: {e}")

        return cargas_criadas

    # -------------------------------------------
    # 2) Baixar XML completo de todos CT-es
    # -------------------------------------------
    async def baixar_ctes_da_carga(self, db: Session, carga: Carga):
        """
        Para cada CT-e sem XML salvo:
        - consulta VBLOG /transito/cte
        - salva XML
        """
        # Importação local para evitar ciclo de importação circular
        from app.services.vblog_cte_service import VBlogCTeService 

        cte_service = VBlogCTeService(self.vblog)

        # Acessa a relação de CT-es da carga
        # Devido ao db.refresh(carga) chamado antes, isso deve estar atualizado
        ctes = carga.ctes_cliente
        atualizados = []

        for cte in ctes:
            # Só baixa se ainda não tiver o XML salvo
            if cte.xml_encrypted is None:
                try:
                    # print(f"Baixando XML para CT-e: {cte.chave}...")
                    xml_raw = await cte_service.baixar_cte(cte.chave)
                    
                    if xml_raw:
                        # Atribui o XML puro. O Model/Setter deve cuidar da criptografia
                        cte.xml = xml_raw 
                        
                        db.add(cte) 
                        db.commit() # Salva cada XML individualmente para garantir persistência
                        atualizados.append(cte)
                    else:
                        print(f"API VBLOG retornou vazio/nulo para o CT-e {cte.chave}")

                except Exception as e:
                    print(f"Erro baixando CT-e {cte.chave}: {e}")

        return atualizados
    
    async def extrair_nfs_cte(self, xml_content: str) -> list:
        """
        Extrai a lista de chaves de NFs associadas ao CT-e.
        Retorna uma lista de strings com as chaves de acesso.
        """
        lista_nfs = []
        
        if not xml_content:
            return lista_nfs

        try:
            # Parseia o XML (transforma string em objeto manipulável)
            root = ET.fromstring(xml_content)

            # Define o dicionário de namespaces encontrados no XML.
            # O link 'http://www.portalfiscal.inf.br/cte' é o padrão para a tag <ns1:CTe>
            namespaces = {
                'cte': 'http://www.portalfiscal.inf.br/cte' 
            }

            # Procura por todas as tags <infNFe> recursivamente (independente da profundidade)
            # Sintaxe: .// procura em todos os descendentes
            elementos_nfe = root.findall('.//cte:infNFe', namespaces)

            for elemento in elementos_nfe:
                # Dentro de <infNFe>, busca a tag <chave>
                chave = elemento.find('cte:chave', namespaces)
                
                if chave is not None and chave.text:
                    lista_nfs.append(chave.text)
            
            return lista_nfs

        except ET.ParseError as e:
            print(f"Erro ao processar estrutura do XML: {e}")
            return []
        except Exception as e:
            print(f"Erro inesperado ao extrair NFs: {e}")
            return []
        
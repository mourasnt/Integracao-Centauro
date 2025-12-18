# app/services/transito_integration_service.py

from typing import Optional
from sqlalchemy.orm import Session

from app.services.carga_service import CargaService
from app.services.cte_cliente_service import CTeClienteService
from app.models.carga import Carga
from app.schemas.carga import CargaCreate

from app.schemas.cte_cliente import CTeClienteCreate
from app.services.localidades_service import LocalidadesService

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
        """
        Consulta /transito/aberto na VBLOG,
        cria cargas e registra CT-es encontrados.
        Retorna lista de cargas criadas ou atualizadas.
        """

        resposta: RetornoControleTransito = await self.vblog.consultar_transito_aberto()

        if resposta.codigo is None:
            print("Erro ao consultar trânsitos abertos na VBLOG")
            return []  # API retornou erro ou vazio

        cargas_criadas = []

        for transito in resposta.transitos:

            xDocTransp = transito.xDocTransp

            if not xDocTransp:
                continue

            # Verifica se já existe carga no banco
            carga = self.obter_carga_por_doc(db, xDocTransp)

            if not carga:
                # Criar nova carga
                id_cliente=xDocTransp
                origem_uf= {
                    "cod": transito.other.get("cUFIni"),
                    "uf": LocalidadesService.get_estado_por_codigo(transito.other.get("cUFIni"))
                }
                origem_municipio= {
                    "cod": transito.other.get("cMunIni"),
                    "municipio": LocalidadesService.get_municipio_por_codigo(transito.other.get("cMunIni"))
                }
                destino_uf= {
                    "cod": transito.other.get("cUFFim"),
                    "uf": LocalidadesService.get_estado_por_codigo(transito.other.get("cUFFim"))
                }
                destino_municipio= {
                    "cod": transito.other.get("cMunFim"),
                    "municipio": LocalidadesService.get_municipio_por_codigo(transito.other.get("cMunFim"))
                }
                
                carga = CargaService.criar_carga(
                    db,
                    CargaCreate(
                        id_cliente=id_cliente,
                        origem_uf=origem_uf,
                        origem_municipio=origem_municipio,
                        destino_uf=destino_uf,
                        destino_municipio=destino_municipio,
                    ),
                )
                cargas_criadas.append(carga)

            # Registrar CT-es (apenas chaves)
            for doc in transito.docs:
                if doc.tipo == "chaveCTe" and doc.valor:
                    chave = doc.valor.strip()

                    # Evitar duplicações
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

        return cargas_criadas

    # -------------------------------------------
    # 2) Baixar XML completo de todos CT-es
    # -------------------------------------------
    async def baixar_ctes_da_carga(self, db: Session, carga: Carga):
        """
        Para cada CT-e sem XML salvo:
        - consulta VBLOG /transito/cte
        - salva XML criptografado
        """
        from app.services.vblog_cte_service import VBlogCTeService  # criaremos depois

        cte_service = VBlogCTeService(self.vblog)

        ctes = carga.ctes_cliente

        atualizados = []

        for cte in ctes:
            if cte.xml_encrypted is None:
                try:
                    xml_raw = await cte_service.baixar_cte(cte.chave)
                    cte.xml = xml_raw  # dispara criptografia
                    db.commit()
                    atualizados.append(cte)
                except Exception as e:
                    print(f"Erro baixando CT-e {cte.chave}: {e}")

        return atualizados

# app/services/cte_sub_service.py

from sqlalchemy.orm import Session
from uuid import UUID

from app.models.cte_subcontratacao import CTeSubcontratacao
from app.schemas.cte_subcontratacao import CTeSubCreate


class CTeSubcontratacaoService:

    @staticmethod
    def adicionar_subcte(
        db: Session,
        carga_id: UUID,
        data: CTeSubCreate
    ) -> CTeSubcontratacao:

        sub = CTeSubcontratacao(
            carga_id=carga_id,
            chave=data.chave,
            cte_cliente_id=data.cte_cliente_id
        )

        sub.xml = data.xml  # criptografia automática

        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def listar_por_carga(db: Session, carga_id: UUID):
        return db.query(CTeSubcontratacao).filter(
            CTeSubcontratacao.carga_id == carga_id
        ).all()

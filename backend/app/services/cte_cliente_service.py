# app/services/cte_cliente_service.py

from sqlalchemy.orm import Session
from uuid import UUID

from app.models.cte_cliente import CTeCliente
from app.schemas.cte_cliente import CTeClienteCreate


class CTeClienteService:

    @staticmethod
    def adicionar_cte(db: Session, carga_id: UUID, data: CTeClienteCreate) -> CTeCliente:
        cte = CTeCliente(
            carga_id=carga_id,
            chave=data.chave,
        )
        cte.xml = data.xml  # dispara criptografia
        db.add(cte)
        db.commit()
        db.refresh(cte)
        return cte

    @staticmethod
    def listar_por_carga(db: Session, carga_id: UUID):
        return db.query(CTeCliente).filter(CTeCliente.carga_id == carga_id).all()

    @staticmethod
    def obter_por_id(db: Session, cte_id: UUID):
        return db.query(CTeCliente).filter(CTeCliente.id == cte_id).first()

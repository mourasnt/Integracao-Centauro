# app/services/agendamento_service.py

from sqlalchemy.orm import Session
from uuid import UUID

from app.models.agendamento import Agendamento
from app.schemas.agendamento import AgendamentoCreate


class AgendamentoService:

    @staticmethod
    def criar_ou_atualizar(db: Session, data: AgendamentoCreate) -> Agendamento:
        ag = db.query(Agendamento).filter(
            Agendamento.carga_id == data.carga_id
        ).first()

        if ag:
            # update
            for campo, valor in data.dict(exclude_unset=True).items():
                setattr(ag, campo, valor)
        else:
            ag = Agendamento(**data.dict())
            db.add(ag)

        db.commit()
        db.refresh(ag)
        return ag

    @staticmethod
    def obter_por_carga(db: Session, carga_id: UUID):
        return db.query(Agendamento).filter(
            Agendamento.carga_id == carga_id
        ).first()

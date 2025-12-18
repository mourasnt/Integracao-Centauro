import datetime
from sqlalchemy.orm import Session

from app.models.tracking import Tracking
from app.models.cte_cliente import CTeCliente
from app.schemas.tracking import TrackingCreate

class TrackingService:

    @staticmethod
    def registrar(db: Session, data: TrackingCreate) -> Tracking:
        tracking = Tracking(**data.dict())
        db.add(tracking)
        db.commit()
        db.refresh(tracking)
        return tracking

    @staticmethod
    def listar_por_cte(db: Session, cte_id):
        return db.query(Tracking).filter(Tracking.cte_cliente_id == cte_id).all()

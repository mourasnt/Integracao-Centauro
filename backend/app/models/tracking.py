from __future__ import annotations
import uuid
import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime, ForeignKey

from .base import Base

class Tracking(Base):
    __tablename__ = "tracking"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    cte_cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cte_cliente.id", ondelete="CASCADE"),
        nullable=False,
    )

    codigo_evento: Mapped[str] = mapped_column(String(10), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)

    data_evento: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(datetime.timezone.utc))

    cte_cliente = relationship("CTeCliente", back_populates="trackings")

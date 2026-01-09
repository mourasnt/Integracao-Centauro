from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config.settings import ATTACHMENTS_DIR, ATTACHMENT_BASE_URL
from app.routes.cargas import router as cargas_router
from app.routes.agendamentos import router as agendamentos_router
from app.routes.subcontratacao import router as subcontratacao_router
from app.routes.tracking import router as tracking_router
from app.routes.localidades import router as localidades_router
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

app = FastAPI()

# ensure attachments directory exists before mounting
Path(ATTACHMENTS_DIR).mkdir(parents=True, exist_ok=True)

# serve attachments uploaded via AttachmentService
app.mount(ATTACHMENT_BASE_URL, StaticFiles(directory=ATTACHMENTS_DIR), name="attachments")

from app.models.base import Base
from app.core.database import engine

@app.on_event("startup")
def create_tables():
    """Cria as tabelas no banco de dados automaticamente na inicialização."""
    # Operação idempotente: não recria tabelas que já existem
    Base.metadata.create_all(bind=engine)
app.include_router(cargas_router)
app.include_router(agendamentos_router)
app.include_router(subcontratacao_router)
app.include_router(tracking_router)
app.include_router(localidades_router)

origins = [
    "http://localhost:3000",     # Next.js local
    "http://127.0.0.1:3000",
    "http://192.168.128.1:3000", # Rede local (ajuste conforme necessário)
    "https://seu-dominio.com",   # produção (opcional)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # libera só origens permitidas
    allow_credentials=True,          # permite cookies / tokens
    allow_methods=["*"],             # libera todos os métodos (GET, POST, etc)
    allow_headers=["*"],             # libera todos os headers
)
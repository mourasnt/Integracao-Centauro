from fastapi import FastAPI
from fastapi import FastAPI
from app.routes.users import router as users_router
from app.routes.cargas import router as cargas_router
from app.routes.agendamentos import router as agendamentos_router
from app.routes.subcontratacao import router as subcontratacao_router
from app.routes.tracking import router as tracking_router
from app.routes.localidades import router as localidades_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(users_router)
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
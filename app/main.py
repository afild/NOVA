import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api.router import api_router
from app.api.websockets import router as ws_router
from app.database.db_manager import init_db
from app.config import settings

# Configuração básica de logging do sistema
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ lifespan do FastAPI que roda tarefas na inicialização e encerramento do servidor. """
    logging.info("[FastAPI lifespan] Inicializando recursos...")
    # Garante a inicialização das tabelas no SQLite
    init_db()
    yield
    logging.info("[FastAPI lifespan] Finalizando recursos...")

app = FastAPI(
    title="NOVA API",
    description="Net Asset & Opportunity Valuation Agent Backend",
    version="0.2.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Configuração de CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Registra as rotas da API
app.include_router(api_router, prefix="/api")

# Registra rotas de WebSocket
app.include_router(ws_router)

# Redireciona a rota raiz para o index do dashboard estático
@app.get("/")
def redirect_to_dashboard():
    return RedirectResponse(url="/static/index.html")

# Servindo o Frontend Estático
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    logging.info(f"[FastAPI Static] Pasta frontend montada com sucesso em /static. Origem: {frontend_dir}")
else:
    logging.warning(f"[FastAPI Static] Diretório frontend não encontrado no caminho {frontend_dir}. Estáticos não montados.")

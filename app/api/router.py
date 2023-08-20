from fastapi import APIRouter
from app.api.assets import router as assets_router
from app.api.analysis import router as analysis_router
from app.api.compare import router as compare_router
from app.api.system import router as system_router

api_router = APIRouter()

# Agrupa as rotas no prefixo global /api
api_router.include_router(assets_router)
api_router.include_router(analysis_router)
api_router.include_router(compare_router)
api_router.include_router(system_router)

"""FastAPI application — Controle Financeiro API."""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

# Configurar logging para ver erros no Render
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from app.routers.auth import router as auth_router
from app.routers.bancos import router as bancos_router
from app.routers.cartoes import router as cartoes_router
from app.routers.categorias import router as categorias_router
from app.routers.despesas import router as despesas_router
from app.routers.receitas import router as receitas_router
from app.routers.frota import router as frota_router
from app.routers.investimentos import router as investimentos_router
from app.routers.orcamento import router as orcamento_router
from app.routers.transferencias import router as transferencias_router
from app.routers.dashboard import router as dashboard_router
from app.routers.relatorios import router as relatorios_router
from app.routers.ferramentas import router as ferramentas_router
from app.routers.migrar_integracoes import router as migrar_router
from app.routers.assinaturas import router as assinaturas_router
from app.routers.webhooks import router as webhooks_router
from app.routers.admin import router as admin_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# CORS — permite apenas o domínio do frontend
logger.info("CORS origins configuradas: %s", settings.cors_origins_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(bancos_router, prefix="/api/v1/bancos", tags=["bancos"])
app.include_router(categorias_router, prefix="/api/v1/categorias", tags=["categorias"])
app.include_router(despesas_router, prefix="/api/v1/despesas", tags=["despesas"])
app.include_router(receitas_router, prefix="/api/v1/receitas", tags=["receitas"])
app.include_router(transferencias_router, prefix="/api/v1/transferencias", tags=["transferencias"])
app.include_router(cartoes_router, prefix="/api/v1/cartoes", tags=["cartoes"])
app.include_router(investimentos_router, prefix="/api/v1/investimentos", tags=["investimentos"])
app.include_router(frota_router, prefix="/api/v1/frota", tags=["frota"])
app.include_router(orcamento_router, prefix="/api/v1/orcamento", tags=["orcamento"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(relatorios_router, prefix="/api/v1/relatorios", tags=["relatorios"])
app.include_router(ferramentas_router, prefix="/api/v1/ferramentas", tags=["ferramentas"])
app.include_router(migrar_router, prefix="/api/v1/migrar", tags=["migração"])
app.include_router(assinaturas_router, prefix="/api/v1/assinaturas", tags=["assinaturas"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura exceções não tratadas e retorna JSON padronizado."""
    logger.error("Erro não tratado em %s %s: %s", request.method, request.url.path, exc)
    logger.error("Traceback: %s", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


@app.get("/api/v1/health")
async def health_check() -> dict:
    """Endpoint de health check."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/api/v1/health/db")
async def db_health_check() -> dict:
    """Testa conexão com o banco de dados."""
    from app.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("Erro de conexão com banco: %s", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "database": str(e)},
        )

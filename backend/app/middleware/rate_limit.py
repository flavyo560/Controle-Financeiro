"""Rate limiting — 100 requisições/minuto por usuário autenticado."""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.middleware.auth import decode_jwt


def _get_rate_limit_key(request: Request) -> str:
    """Extrai chave de rate limit: user_id do JWT ou IP remoto."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_jwt(token)
        if payload and payload.get("user_id"):
            return f"user:{payload['user_id']}"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, default_limits=["100/minute"])


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Handler para HTTP 429 quando rate limit é excedido."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Limite de requisições excedido. Tente novamente em breve."},
    )

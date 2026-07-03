"""FastAPI application entrypoint.

Wires middleware (CORS, rate limiting), the v1 router, health checks, and DB
initialisation on startup. Run with:

    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.db.init_db import init_db

logger = get_logger("app.main")

# Global rate limiter (per client IP). Tune per-route with @limiter.limit(...).
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.ENVIRONMENT, provider=settings.LLM_PROVIDER)
    init_db()
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Autonomous multi-agent career assistant (LangGraph + Azure OpenAI).",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# NOTE: middleware added LAST is outermost. We add the catch-all FIRST and CORS
# LAST so the stack is: CORS -> catch-all -> router. That way an unhandled
# exception is converted to a JSON 500 *inside* the CORS layer, so the response
# still carries Access-Control-Allow-Origin and the browser shows the real error
# instead of a misleading "No 'Access-Control-Allow-Origin' header" CORS failure.
@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001 - last-resort safety net
        logger.error("request.unhandled", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    # Convert domain validation errors into clean 400s.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": settings.APP_NAME, "provider": settings.LLM_PROVIDER}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

"""
DeckDex MTG - FastAPI Backend
Main application entry point
"""
import os
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys

# Configure loguru logger
logger.remove()  # Remove default handler

_is_dev = os.getenv("DECKDEX_PROFILE", "default") in ("default", "development")

# stderr: human-readable in dev, JSON in production
if _is_dev:
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
else:
    logger.add(sys.stderr, serialize=True, level="INFO")

# File: always structured JSON for log aggregation / SIEM ingestion
logger.add(
    "logs/api.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    serialize=True,
)

# Rate limiter (in-memory storage, keyed by remote address by default)
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="DeckDex MTG API",
    description="REST API for DeckDex MTG card collection management",
    version="0.1.0"
)

# Attach limiter to app state (required by slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS (configurable via environment)
_cors_origins_raw = os.getenv("DECKDEX_CORS_ORIGINS", "http://localhost:5173")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
logger.info(f"CORS allowed origins: {_cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for unhandled exceptions — NO internal details leaked
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

# ---------------------------------------------------------------------------
# Global request body size limit (25 MB)
# ---------------------------------------------------------------------------
_MAX_BODY_SIZE = 25 * 1024 * 1024  # 25 MB


@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_BODY_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Request body too large (max 25MB)"},
        )
    return await call_next(request)


# ---------------------------------------------------------------------------
# Request ID + logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_and_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    # Stash on request state so downstream handlers/logs can use it
    request.state.request_id = request_id

    logger.info(f"{request.method} {request.url.path} [rid={request_id}]")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"{request.method} {request.url.path} - {response.status_code} [rid={request_id}]")
    return response


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not _is_dev:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


logger.info("DeckDex MTG API started")


# ---------------------------------------------------------------------------
# Deep health check (verifies DB connectivity)
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    result = {
        "service": "DeckDex MTG API",
        "version": "0.1.0",
        "status": "healthy",
        "database": "not_configured",
    }
    try:
        from .db import get_engine
        engine = get_engine()
        if engine is not None:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            result["database"] = "connected"
        else:
            result["database"] = "not_configured"
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        result["status"] = "degraded"
        result["database"] = "error"
        return JSONResponse(status_code=503, content=result)
    return result

# Import and include routers
from .routes import cards, stats, process, import_routes, settings_routes, analytics, decks, auth, insights, catalog_routes, admin_routes
from .websockets import progress

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(stats.router)
app.include_router(process.router)
app.include_router(import_routes.router_import)
app.include_router(settings_routes.router)
app.include_router(analytics.router)
app.include_router(decks.router)
app.include_router(insights.router)
app.include_router(catalog_routes.router)
app.include_router(admin_routes.router)
app.include_router(progress.router)

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    from .db import dispose_engine
    dispose_engine()
    logger.info("API shutting down")

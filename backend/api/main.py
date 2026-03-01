"""
DeckDex MTG - FastAPI Backend
Main application entry point
"""
import os
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
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/api.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
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

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response

logger.info("DeckDex MTG API started")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "service": "DeckDex MTG API",
        "version": "0.1.0",
        "status": "healthy"
    }

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

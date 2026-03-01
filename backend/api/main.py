"""
DeckDex MTG - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
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

# Initialize FastAPI app
app = FastAPI(
    title="DeckDex MTG API",
    description="REST API for DeckDex MTG card collection management",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions
    
    Returns 500 Internal Server Error with logging
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors
    
    Returns 400 Bad Request with validation details
    """
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
    """
    Log all API requests with endpoint, method, and response status
    """
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response

logger.info("DeckDex MTG API started")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    Returns service name and version
    """
    return {
        "service": "DeckDex MTG API",
        "version": "0.1.0",
        "status": "healthy"
    }

# Import and include routers
from .routes import cards, stats, process, import_routes, settings_routes, analytics, decks, auth, insights, catalog_routes
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
app.include_router(progress.router)

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("API shutting down")

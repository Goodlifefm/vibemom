"""
FastAPI Mini App API Service.

Production-ready API for Telegram Mini App with:
- Telegram WebApp initData authentication
- JWT session management
- Project management endpoints
- Strict CORS configuration
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.db import close_db, get_engine
from app.logging_config import get_logger, setup_logging
from app.routers import auth_router, debug_router, health_router, me_router, projects_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info(f"Starting Mini App API v{__version__}")

    # Initialize database engine
    settings = get_settings()
    logger.info(f"Environment: {settings.app_env}")

    # Warm up database connection
    try:
        from sqlalchemy import text
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Mini App API")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Vibe Market Mini App API",
    description="REST API for Telegram Mini App",
    version=__version__,
    docs_url="/docs" if not get_settings().is_production else None,
    redoc_url="/redoc" if not get_settings().is_production else None,
    lifespan=lifespan,
)


# =============================================================================
# CORS Configuration
# =============================================================================
# Supports:
# - Explicit origins from env (ALLOWED_ORIGINS, WEBAPP_URL, etc.)
# - Regex for *.vercel.app and vibemom.ru subdomains
# - Dev origins (localhost:5173)
# - Telegram origins (web.telegram.org, t.me)

settings = get_settings()
cors_origins = settings.get_cors_origins()
cors_origin_regex = settings.get_cors_origin_regex()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    # credentials=False: Telegram Mini App never sends cookies/credentials.
    # This avoids the spec restriction that forbids wildcard origins with credentials.
    allow_credentials=False,
    allow_methods=["*"],
    # Telegram WebView request headers can vary (case, extra headers). Allow all to avoid preflight failures.
    allow_headers=["*"],
    expose_headers=["X-API-Version"],
)
logger.info(f"CORS enabled for origins: {cors_origins}")
logger.info(f"CORS origin regex: {cors_origin_regex}")


# =============================================================================
# Global Exception Handlers
# =============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


# =============================================================================
# Middleware
# =============================================================================


@app.middleware("http")
async def add_api_version_header(request: Request, call_next):
    """Add API version header to all responses."""
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


@app.middleware("http")
async def cors_diagnostic_logging(request: Request, call_next):
    """Log CORS diagnostic info for debugging cross-origin requests."""
    origin = request.headers.get("origin", "-")
    path = request.url.path
    method = request.method
    
    # Extract user_id from Authorization header if present (for diagnostics only)
    user_id = "-"
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            token = auth_header[7:]
            # Decode without verification just to extract user_id for logging
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = str(payload.get("sub", "-"))
        except Exception:
            pass
    
    # Log cross-origin traffic for non-health endpoints.
    if origin != "-" and path not in ["/healthz", "/", "/docs", "/openapi.json"]:
        if method == "OPTIONS":
            acr_method = request.headers.get("access-control-request-method", "-")
            acr_headers = request.headers.get("access-control-request-headers", "-")
            logger.info(
                f"CORS preflight: origin={origin} path={path} "
                f"request_method={acr_method} request_headers={acr_headers}"
            )
        else:
            # Log key endpoints at INFO so we can confirm real WebView traffic in production logs.
            if path in ['/projects/my', '/auth/telegram']:
                logger.info(f"CORS: origin={origin} method={method} path={path} user_id={user_id}")
            else:
                logger.debug(f"CORS: origin={origin} method={method} path={path} user_id={user_id}")
    
    response = await call_next(request)
    return response


# =============================================================================
# Include Routers
# =============================================================================

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(projects_router)
app.include_router(debug_router)


# =============================================================================
# Root Endpoint
# =============================================================================


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "service": "Vibe Market Mini App API",
        "version": __version__,
        "docs": "/docs",
        "health": "/healthz",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

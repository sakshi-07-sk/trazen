"""CryptoTrace FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cryptotrace.api.v1.endpoints.health import router as root_health_router
from cryptotrace.api.v1.router import api_v1_router
from cryptotrace.config import get_settings
from cryptotrace.core.exceptions import CryptoTraceException
from cryptotrace.core.logging import logger, setup_logging
from cryptotrace.db.session import init_db

settings = get_settings()
setup_logging(debug=settings.APP_DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown life cycle events."""
    logger.info("Initializing CryptoTrace Engine...")
    try:
        await init_db()
        logger.info("Database schemas verified.")
    except Exception as e:
        logger.error(f"Failed to initialize database during startup: {e}")
    yield
    logger.info("CryptoTrace Engine shutting down.")


app = FastAPI(
    title="CryptoTrace — Blockchain Forensics & Threat Intelligence",
    description=(
        "Production-grade blockchain forensic data foundation providing multi-chain ingestion, "
        "UTXO and Account canonical normalization, NetworkX multi-hop transaction graph construction, "
        "and investigation APIs."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(CryptoTraceException)
async def cryptotrace_exception_handler(request: Request, exc: CryptoTraceException) -> JSONResponse:
    logger.warning(f"CryptoTrace error [{exc.code}] on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Request validation failure on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters or payload",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred",
            "details": {"exception_type": type(exc).__name__},
        },
    )


# Root health endpoint (/health) as required by specification
app.include_router(root_health_router)

# Versioned API routes (/api/v1/...)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cryptotrace.main:app", host=settings.HOST, port=settings.PORT, reload=settings.APP_DEBUG)

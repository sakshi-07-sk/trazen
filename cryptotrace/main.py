"""CryptoTrace FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cryptotrace.api.v1.endpoints.health import router as root_health_router
from cryptotrace.api.v1.router import api_v1_router
from cryptotrace.config import get_settings
from cryptotrace.core.exceptions import CryptoTraceException
from cryptotrace.core.logging import logger, setup_logging
from cryptotrace.core.middleware import (
    RateLimitHTTPMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    SlidingWindowRateLimiter,
)
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

# Explicit CORS Middleware (wildcards rejected by Settings validator)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)

# Role 3 Security Hardening Middlewares
rate_limiter = SlidingWindowRateLimiter(requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
app.state.rate_limiter = rate_limiter
app.add_middleware(RateLimitHTTPMiddleware, limiter=rate_limiter)
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_BYTES)
app.add_middleware(SecurityHeadersMiddleware)


# Global Exception Handlers (preserving Team error envelope + adding correlation_id & sanitization)
@app.exception_handler(CryptoTraceException)
async def cryptotrace_exception_handler(request: Request, exc: CryptoTraceException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    logger.warning(f"CryptoTrace error [{exc.code}] [{correlation_id}] on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    logger.warning(f"Request validation failure [{correlation_id}] on {request.method} {request.url.path}: {exc}")
    sanitized_errors = [
        {
            "loc": err.get("loc", []),
            "msg": err.get("msg", "Invalid field"),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters or payload",
            "details": sanitized_errors,
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    logger.error(f"Unhandled exception [{correlation_id}] on {request.method} {request.url.path}: {type(exc).__name__}", exc_info=settings.APP_DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred",
            "details": {"exception_type": type(exc).__name__} if settings.APP_DEBUG else {},
            "correlation_id": correlation_id,
        },
    )


# Root health endpoint (/health) as required by specification
app.include_router(root_health_router)

# Versioned API routes (/api/v1/...)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cryptotrace.main:app", host=settings.HOST, port=settings.PORT, reload=settings.APP_DEBUG)

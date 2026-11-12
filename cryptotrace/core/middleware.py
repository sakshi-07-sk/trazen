"""FastAPI security hardening middleware: size limits, rate limiting, headers, and secret checks."""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from cryptotrace.core.logging_utils import get_security_logger

_LOGGER = get_security_logger()

FORBIDDEN_WALLET_SECRET_KEYS: frozenset[str] = frozenset(
    {"private_key", "seed_phrase", "mnemonic", "wallet_secret", "recovery_phrase"}
)


def contains_forbidden_wallet_secrets(payload: Any) -> str | None:
    """Recursively check if a decoded request body attempts to transmit private keys or seed phrases."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            key_norm = str(k).strip().lower()
            if key_norm in FORBIDDEN_WALLET_SECRET_KEYS and v not in (None, "", []):
                return key_norm
            nested = contains_forbidden_wallet_secrets(v)
            if nested:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = contains_forbidden_wallet_secrets(item)
            if nested:
                return nested
    return None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach defensive HTTP response headers and correlation IDs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        # Allow Swagger/ReDoc UI assets on /docs and /redoc while locking down API responses
        if request.url.path in ("/docs", "/redoc", "/openapi.json"):
            response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        else:
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized HTTP request payloads and wallet secret submissions early."""

    def __init__(self, app: Any, max_bytes: int = 1_048_576) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        content={
                            "error": "PAYLOAD_TOO_LARGE",
                            "message": "Request payload exceeds maximum allowed size.",
                            "detail": "Request payload exceeds maximum allowed size.",
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "INVALID_CONTENT_LENGTH",
                        "message": "Invalid Content-Length header.",
                        "detail": "Invalid Content-Length header.",
                    },
                )

        body = await request.body()
        if len(body) > self.max_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={
                    "error": "PAYLOAD_TOO_LARGE",
                    "message": "Request payload exceeds maximum allowed size.",
                    "detail": "Request payload exceeds maximum allowed size.",
                },
            )
        if body and "application/json" in (request.headers.get("content-type") or "").lower():
            try:
                parsed = json.loads(body)
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "MALFORMED_JSON",
                        "message": "Malformed JSON request payload.",
                        "detail": "Malformed JSON request payload.",
                    },
                )
            forbidden_key = contains_forbidden_wallet_secrets(parsed)
            if forbidden_key:
                _LOGGER.warning(
                    "Rejected request containing forbidden wallet secret field '%s'", forbidden_key
                )
                msg = "CryptoTrace never accepts private keys, seed phrases, or wallet signing secrets."
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "FORBIDDEN_WALLET_SECRET",
                        "message": msg,
                        "detail": msg,
                    },
                )
        return await call_next(request)


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter keyed by client identity."""

    def __init__(self, requests_per_minute: int = 120) -> None:
        self.requests_per_minute = max(1, requests_per_minute)
        self._lock = threading.Lock()
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def check_allowed(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.requests_per_minute:
                retry_after = max(1, int(60.0 - (now - bucket[0])) + 1)
                return False, retry_after
            bucket.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear tracked rate-limit buckets (for isolated tests)."""
        with self._lock:
            self._buckets.clear()


class RateLimitHTTPMiddleware(BaseHTTPMiddleware):
    """Clean HTTP 429 rate-limiter middleware."""

    def __init__(self, app: Any, limiter: SlidingWindowRateLimiter) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.endswith("/health"):
            return await call_next(request)
        client_host = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("authorization", "")
        key = f"{client_host}:{hash(auth_header) if auth_header else 'anon'}"
        allowed, retry_after = self.limiter.check_allowed(key)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Retry later.",
                    "detail": "Rate limit exceeded. Retry later.",
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


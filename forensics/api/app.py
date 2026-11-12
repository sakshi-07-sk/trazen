"""FastAPI application factory for CryptoTrace Forensic Intelligence Engine."""

from __future__ import annotations

from fastapi import FastAPI

from forensics.api.router import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="CryptoTrace Forensic Intelligence Engine",
        version="1.0.0",
        description="Role 2 explainable blockchain forensics, risk scoring, and ML prioritization API.",
    )
    app.include_router(router)
    return app


app = create_app()

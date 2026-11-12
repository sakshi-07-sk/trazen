"""API v1 Router aggregating endpoints."""

from fastapi import APIRouter
from cryptotrace.api.v1.endpoints.health import router as health_router
from cryptotrace.api.v1.endpoints.investigations import router as investigations_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(investigations_router)

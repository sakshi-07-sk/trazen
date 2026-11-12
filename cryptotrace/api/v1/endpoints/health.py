"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.config import get_settings
from cryptotrace.db.session import get_db
from cryptotrace.schemas.contracts import HealthCheckResponse

router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Reports the operational status of the CryptoTrace backend engine and database connectivity.",
)
async def check_health(session: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
    db_connected = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        version="0.1.0",
        app_env=settings.APP_ENV,
        database_connected=db_connected,
        fixture_mode_enabled=settings.DEMO_FIXTURE_MODE,
    )

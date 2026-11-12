"""FastAPI Request Dependencies."""

import hmac
import os
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.config import get_settings
from cryptotrace.db.session import get_db
from cryptotrace.services.investigation_service import InvestigationService


def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Optional[str]:
    """Validate X-API-Key against comma-separated API_KEYS env/settings."""
    settings = get_settings()
    raw_keys = os.environ.get("API_KEYS", settings.API_KEYS)
    allowed_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

    if not allowed_keys:
        if settings.APP_ENV.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key authentication required.",
            )
        return None

    if not x_api_key or not any(
        hmac.compare_digest(x_api_key, valid) for valid in allowed_keys
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key.",
        )
    return x_api_key


async def get_investigation_service(
    session: AsyncSession = Depends(get_db),
    _api_key: Optional[str] = Depends(verify_api_key),
) -> InvestigationService:
    """Dependency injecting InvestigationService with active database session and auth check."""
    return InvestigationService(session)

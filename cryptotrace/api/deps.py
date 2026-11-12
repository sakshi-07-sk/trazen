"""FastAPI Request Dependencies."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.db.session import get_db
from cryptotrace.services.investigation_service import InvestigationService


async def get_investigation_service(
    session: AsyncSession = Depends(get_db),
) -> InvestigationService:
    """Dependency injecting InvestigationService with active database session."""
    return InvestigationService(session)

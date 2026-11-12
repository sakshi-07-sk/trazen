"""FastAPI Request Dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.config import Settings, get_settings
from cryptotrace.db.session import get_db
from cryptotrace.services.audit.audit_export import AuditExportService
from cryptotrace.services.audit.audit_service import AuditService
from cryptotrace.services.audit.audit_verifier import AuditVerifier
from cryptotrace.services.investigation_service import InvestigationService
from cryptotrace.services.security.security_orchestrator import SecurityOrchestrator


async def get_investigation_service(
    session: AsyncSession = Depends(get_db),
) -> InvestigationService:
    """Dependency injecting InvestigationService with active database session."""
    return InvestigationService(session)


async def get_audit_service(
    session: AsyncSession = Depends(get_db),
) -> AuditService:
    """Dependency injecting async AuditService bound to active database session."""
    return AuditService(session)


async def get_audit_verifier(
    session: AsyncSession = Depends(get_db),
) -> AuditVerifier:
    """Dependency injecting async AuditVerifier bound to active database session."""
    return AuditVerifier(session)


async def get_audit_export_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuditExportService:
    """Dependency injecting AuditExportService with optional Ed25519 signing key."""
    return AuditExportService(
        audit_service=AuditService(session),
        audit_verifier=AuditVerifier(session),
        signing_private_key_pem=settings.AUDIT_SIGNING_PRIVATE_KEY_PEM,
    )


async def get_security_orchestrator(
    session: AsyncSession = Depends(get_db),
) -> SecurityOrchestrator:
    """Dependency injecting SecurityOrchestrator for investigation-level scans."""
    return SecurityOrchestrator(session)

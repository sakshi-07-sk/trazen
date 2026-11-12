"""Role 3 FastAPI router under /api/v1/security."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.api.deps import (
    get_audit_export_service,
    get_audit_service,
    get_audit_verifier,
    get_security_orchestrator,
)
from cryptotrace.config import Settings, get_settings
from cryptotrace.core.auth import AuthContext, enforce_investigation_access, get_auth_context
from cryptotrace.db.session import get_db
from cryptotrace.schemas.audit import (
    AuditEventCreate,
    AuditEventRecord,
    AuditExportManifest,
    AuditVerificationReport,
    AuditVerificationRequest,
)
from cryptotrace.schemas.findings import SecurityFinding, SharedFindingAdapter
from cryptotrace.schemas.security_requests import (
    AddressPoisoningRequest,
    AuditHistoryResponse,
    BlockchainValidationAPIResponse,
    BlockchainValidationRequest,
    DustingAnalysisRequest,
    GraphIntegrityRequest,
    GraphIntegrityResponse,
    InvestigationSecurityScanResponse,
    SecurityFindingsResponse,
    TokenImpersonationRequest,
    TraceAIInspectRequest,
    TraceAIOutputValidationRequest,
    TraceAIToolValidationRequest,
)
from cryptotrace.services.audit.audit_export import AuditExportService
from cryptotrace.services.audit.audit_service import AuditService
from cryptotrace.services.audit.audit_verifier import AuditVerifier
from cryptotrace.services.security.address_poisoning import AddressPoisoningDetector
from cryptotrace.services.security.blockchain_validator import BlockchainDataValidator
from cryptotrace.services.security.dusting_detector import DustingDetector
from cryptotrace.services.security.graph_integrity import GraphIntegrityAnalyzer
from cryptotrace.services.security.security_guardrails import (
    AIOutputValidationResult,
    PromptInspectionResult,
    ToolValidationResult,
    TraceAISecurityGuardrails,
)
from cryptotrace.services.security.security_orchestrator import SecurityOrchestrator
from cryptotrace.services.security.token_impersonation import TokenImpersonationDetector

router = APIRouter(prefix="/security", tags=["Security & Forensic Audit"])


def _build_findings_response(
    investigation_id: str,
    findings: list[SecurityFinding],
) -> SecurityFindingsResponse:
    return SecurityFindingsResponse(
        investigation_id=investigation_id,
        total_findings=len(findings),
        findings=findings,
        shared_findings=[SharedFindingAdapter.to_shared_finding_dict(f) for f in findings],
    )


@router.get("/health")
async def security_health() -> dict[str, str]:
    """Liveness endpoint for the Role 3 security and audit subsystem."""
    return {"status": "ok", "subsystem": "role3-security-audit"}


@router.post(
    "/investigations/{investigation_id}/scan",
    response_model=InvestigationSecurityScanResponse,
)
async def scan_persisted_investigation(
    investigation_id: str,
    include_validation_findings: bool = Query(default=False),
    auth: AuthContext = Depends(get_auth_context),
    orchestrator: SecurityOrchestrator = Depends(get_security_orchestrator),
    audit_service: AuditService = Depends(get_audit_service),
) -> InvestigationSecurityScanResponse:
    """Run all Role 3 detectors and graph integrity verification over an existing investigation."""
    enforce_investigation_access(auth, investigation_id, "run_security_analysis")
    scan = await orchestrator.scan_investigation(
        investigation_id,
        include_validation_findings=include_validation_findings,
    )
    findings = scan["findings"]
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=investigation_id,
            event_type="INVESTIGATION_SECURITY_SCAN",
            payload={
                "blockchain": scan["blockchain"],
                "transactions_evaluated": scan["transactions_evaluated"],
                "tokens_evaluated": scan["tokens_evaluated"],
                "is_integrity_clean": scan["graph_integrity"].is_integrity_clean,
                "findings_count": len(findings),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return InvestigationSecurityScanResponse(
        investigation_id=scan["investigation_id"],
        target_address=scan["target_address"],
        blockchain=scan["blockchain"],
        transactions_evaluated=scan["transactions_evaluated"],
        tokens_evaluated=scan["tokens_evaluated"],
        graph_integrity=asdict(scan["graph_integrity"]),
        validation_summary=scan["validation_summary"],
        total_findings=len(findings),
        findings=findings,
        shared_findings=scan["shared_findings"],
    )


@router.post("/detect/address-poisoning", response_model=SecurityFindingsResponse)
async def detect_address_poisoning(
    payload: AddressPoisoningRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> SecurityFindingsResponse:
    """Detect address poisoning and look-alike wallet spoofing with contextual correlation."""
    enforce_investigation_access(auth, payload.investigation_id, "run_security_analysis")
    detector = AddressPoisoningDetector()
    findings = detector.analyze(
        investigation_id=payload.investigation_id,
        target_wallet=payload.target_wallet,
        chain=payload.chain,
        transactions=payload.transactions,
        known_counterparties=payload.known_counterparties,
        report_uncorroborated_lookalikes=payload.report_uncorroborated_lookalikes,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="ADDRESS_POISONING_SCAN",
            payload={
                "target_wallet": payload.target_wallet,
                "chain": payload.chain,
                "tx_count": len(payload.transactions),
                "findings_count": len(findings),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return _build_findings_response(payload.investigation_id, findings)


@router.post("/detect/dusting", response_model=SecurityFindingsResponse)
async def detect_dusting(
    payload: DustingAnalysisRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> SecurityFindingsResponse:
    """Detect asset-aware dusting patterns while filtering benign small payments."""
    enforce_investigation_access(auth, payload.investigation_id, "run_security_analysis")
    detector = DustingDetector()
    findings = detector.analyze(
        investigation_id=payload.investigation_id,
        transactions=payload.transactions,
        known_exchange_addresses=set(payload.known_exchange_addresses),
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="DUSTING_SCAN",
            payload={
                "tx_count": len(payload.transactions),
                "findings_count": len(findings),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return _build_findings_response(payload.investigation_id, findings)


@router.post("/detect/token-impersonation", response_model=SecurityFindingsResponse)
async def detect_token_impersonation(
    payload: TokenImpersonationRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> SecurityFindingsResponse:
    """Detect counterfeit token symbols, homoglyphs, contract spoofing, and metadata drift."""
    enforce_investigation_access(auth, payload.investigation_id, "run_security_analysis")
    detector = TokenImpersonationDetector()
    findings: list[SecurityFinding] = []
    for token in payload.tokens:
        findings.extend(detector.analyze(investigation_id=payload.investigation_id, token=token))

    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="TOKEN_IMPERSONATION_SCAN",
            payload={
                "tokens_checked": len(payload.tokens),
                "findings_count": len(findings),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return _build_findings_response(payload.investigation_id, findings)


@router.post("/detect/graph-integrity", response_model=GraphIntegrityResponse)
async def detect_graph_integrity(
    payload: GraphIntegrityRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> GraphIntegrityResponse:
    """Validate NetworkX graph edges against supporting transaction and provenance evidence."""
    enforce_investigation_access(auth, payload.investigation_id, "run_security_analysis")
    analyzer = GraphIntegrityAnalyzer()
    summary, findings = analyzer.analyze(
        investigation_id=payload.investigation_id,
        nodes=payload.nodes,
        edges=payload.edges,
        evidence_transactions=payload.evidence_transactions,
        verified_transactions=payload.verified_transactions or None,
        require_node_membership=payload.require_node_membership,
        require_provenance_ref=payload.require_provenance_ref,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="GRAPH_INTEGRITY_SCAN",
            payload={
                "node_count": summary.node_count,
                "edge_count": summary.edge_count,
                "flagged_edge_count": summary.flagged_edge_count,
                "is_integrity_clean": summary.is_integrity_clean,
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return GraphIntegrityResponse(
        investigation_id=payload.investigation_id,
        node_count=summary.node_count,
        edge_count=summary.edge_count,
        validated_edge_count=summary.validated_edge_count,
        flagged_edge_count=summary.flagged_edge_count,
        duplicate_edge_count=summary.duplicate_edge_count,
        is_integrity_clean=summary.is_integrity_clean,
        findings=findings,
    )


@router.post("/validate/blockchain-data", response_model=BlockchainValidationAPIResponse)
async def validate_blockchain_data(
    payload: BlockchainValidationRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
    settings: Settings = Depends(get_settings),
) -> BlockchainValidationAPIResponse:
    """Validate blockchain transaction records and cross-check multi-provider observations."""
    enforce_investigation_access(auth, payload.investigation_id, "run_security_analysis")
    validator = BlockchainDataValidator(
        require_independent_verification=settings.REQUIRE_INDEPENDENT_PROVIDER_VERIFICATION
    )
    report = validator.validate_transaction(
        investigation_id=payload.investigation_id,
        tx=payload.transaction,
        provider_observations=payload.provider_observations,
        require_independent=payload.require_independent_verification,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="BLOCKCHAIN_DATA_VALIDATION",
            payload={
                "tx_hash": payload.transaction.tx_hash,
                "chain": payload.transaction.chain,
                "validation_status": report.validation_status.value,
                "independent_verification_status": report.independent_verification_status.value,
                "conflict_count": len(report.conflicts),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return BlockchainValidationAPIResponse(
        investigation_id=payload.investigation_id,
        report=report,
    )


@router.post("/guardrails/traceai/inspect-input", response_model=PromptInspectionResult)
async def inspect_traceai_input(
    payload: TraceAIInspectRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> PromptInspectionResult:
    """Inspect analyst prompts and untrusted blockchain metadata for prompt injection."""
    enforce_investigation_access(auth, payload.investigation_id, "run_traceai_guardrails")
    guardrails = TraceAISecurityGuardrails()
    result = guardrails.inspect_and_isolate_context(
        investigation_id=payload.investigation_id,
        user_prompt=payload.user_prompt,
        untrusted_items=payload.untrusted_items,
        auth=auth,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="TRACEAI_INPUT_INSPECTION",
            payload={
                "injection_detected": result.injection_detected,
                "is_safe_to_process": result.is_safe_to_process,
                "cross_investigation_blocked": result.cross_investigation_blocked,
                "indicator_count": len(result.matched_indicators),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return result


@router.post("/guardrails/traceai/validate-tool-call", response_model=ToolValidationResult)
async def validate_traceai_tool_call(
    payload: TraceAIToolValidationRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> ToolValidationResult:
    """Gate TraceAI tool invocations against read-only allowlist and investigation access."""
    enforce_investigation_access(auth, payload.investigation_id, "run_traceai_guardrails")
    guardrails = TraceAISecurityGuardrails()
    result = guardrails.validate_tool_call(
        investigation_id=payload.investigation_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        auth=auth,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="TRACEAI_TOOL_GATE",
            payload={
                "tool_name": payload.tool_name,
                "allowed": result.allowed,
                "violations": result.violations,
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return result


@router.post("/guardrails/traceai/validate-output", response_model=AIOutputValidationResult)
async def validate_traceai_output(
    payload: TraceAIOutputValidationRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> AIOutputValidationResult:
    """Validate TraceAI responses for leakage, fabricated citations, and epistemic labeling."""
    enforce_investigation_access(auth, payload.investigation_id, "run_traceai_guardrails")
    guardrails = TraceAISecurityGuardrails()
    result = guardrails.validate_ai_output(
        investigation_id=payload.investigation_id,
        response_text=payload.response_text,
        cited_evidence_refs=payload.cited_evidence_refs,
        allowed_evidence_refs=set(payload.allowed_evidence_refs),
        epistemic_label=payload.epistemic_label,
        auth=auth,
    )
    await audit_service.record_event(
        AuditEventCreate(
            investigation_id=payload.investigation_id,
            event_type="TRACEAI_OUTPUT_VALIDATION",
            payload={
                "approved": result.approved,
                "epistemic_label": result.epistemic_label.value,
                "ungrounded_count": len(result.ungrounded_citations),
            },
        ),
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )
    return result


@router.post(
    "/audit/events",
    response_model=AuditEventRecord,
    status_code=status.HTTP_201_CREATED,
)
async def append_audit_event(
    payload: AuditEventCreate,
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditEventRecord:
    """Append an authorized, tamper-evident SHA-256 hash-chained audit event."""
    enforce_investigation_access(auth, payload.investigation_id, "write_audit")
    return await audit_service.record_event(
        payload,
        actor_override=auth.actor_id,
        actor_role_override=auth.role,
    )


@router.post("/audit/verify", response_model=AuditVerificationReport)
async def verify_audit_chain(
    payload: AuditVerificationRequest,
    auth: AuthContext = Depends(get_auth_context),
    audit_verifier: AuditVerifier = Depends(get_audit_verifier),
) -> AuditVerificationReport:
    """Verify SHA-256 hash-chain continuity, ordering, and payload digests for an investigation."""
    enforce_investigation_access(auth, payload.investigation_id, "verify_audit")
    return await audit_verifier.verify_investigation(
        payload.investigation_id,
        expected_event_count=payload.expected_event_count,
        expected_head_hash=payload.expected_head_hash,
    )


@router.get("/audit/{investigation_id}", response_model=AuditHistoryResponse)
async def get_audit_history(
    investigation_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditHistoryResponse:
    """Retrieve investigation-scoped tamper-evident audit events."""
    enforce_investigation_access(auth, investigation_id, "read_audit")
    events = await audit_service.list_events(
        investigation_id=investigation_id,
        limit=limit,
        offset=offset,
    )
    return AuditHistoryResponse(
        investigation_id=investigation_id,
        total_returned=len(events),
        events=events,
    )


@router.get("/audit/{investigation_id}/export", response_model=AuditExportManifest)
async def export_audit_history(
    investigation_id: str,
    auth: AuthContext = Depends(get_auth_context),
    exporter: AuditExportService = Depends(get_audit_export_service),
) -> AuditExportManifest:
    """Export a self-contained, verifiable (and optionally Ed25519-signed) audit manifest."""
    enforce_investigation_access(auth, investigation_id, "export_audit")
    return await exporter.export_investigation(investigation_id)


# Ensure AsyncSession dependency import stays discoverable for FastAPI type inspection
_SESSION_DEP = get_db
_SESSION_TYPE = AsyncSession

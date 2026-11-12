"""FastAPI router exposing Role 2 forensic intelligence contracts."""

from __future__ import annotations

import hmac
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from forensics.api.store import CaseConflictError, InMemoryInvestigationStore
from forensics.datasets.synthetic_ml import generate_synthetic_ml_dataset
from forensics.engine import ForensicEngine
from forensics.ml.evaluation import evaluate_ml_models
from forensics.schemas.input import InvestigationCase
from forensics.schemas.output import (
    CrossCaseAnalysisResponse,
    ForensicAnalysisBundle,
    InvestigationFindingsResponse,
    MLEvaluationReport,
    RiskAssessmentResponse,
)


MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_CROSS_CASE_COUNT = 10


def verify_forensics_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Optional[str]:
    """Enforce X-API-Key when API_KEYS env var is configured (or in production)."""
    raw_keys = os.environ.get("API_KEYS", "")
    allowed_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not allowed_keys:
        if os.environ.get("APP_ENV", "development").lower() == "production":
            raise HTTPException(status_code=401, detail="API key authentication required.")
        return None
    if not x_api_key or not any(hmac.compare_digest(x_api_key, k) for k in allowed_keys):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key.")
    return x_api_key


async def enforce_max_body_size(request: Request) -> None:
    """Reject requests exceeding 2MB with HTTP 413."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                raise HTTPException(status_code=413, detail="Request body exceeds 2MB limit.")
        except ValueError:
            pass
    body = await request.body()
    if len(body) > MAX_REQUEST_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body exceeds 2MB limit.")


router = APIRouter(
    prefix="/api/v1",
    tags=["forensics"],
    dependencies=[Depends(verify_forensics_api_key)],
)

_DEFAULT_STORE = InMemoryInvestigationStore(preload_demo_cases=True)
_DEFAULT_ENGINE = ForensicEngine()


def get_store() -> InMemoryInvestigationStore:
    return _DEFAULT_STORE


def get_engine() -> ForensicEngine:
    return _DEFAULT_ENGINE


class CrossCaseRequest(BaseModel):
    case_ids: List[str] = []
    cases: List[InvestigationCase] = []


@router.get(
    "/investigations/{investigation_id}/findings",
    response_model=InvestigationFindingsResponse,
)
def get_investigation_findings(
    investigation_id: str,
    store: InMemoryInvestigationStore = Depends(get_store),
    engine: ForensicEngine = Depends(get_engine),
) -> InvestigationFindingsResponse:
    """Return explainable forensic findings and candidate wallet clusters for an investigation."""
    bundle = store.get_or_compute_analysis(investigation_id, engine)
    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return bundle.findings_response


@router.get(
    "/investigations/{investigation_id}/risk",
    response_model=RiskAssessmentResponse,
)
def get_investigation_risk(
    investigation_id: str,
    store: InMemoryInvestigationStore = Depends(get_store),
    engine: ForensicEngine = Depends(get_engine),
) -> RiskAssessmentResponse:
    """Return 4-dimensional explainable risk assessment and probable end-receiver ranking."""
    bundle = store.get_or_compute_analysis(investigation_id, engine)
    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return bundle.risk_response


@router.post(
    "/investigations/{investigation_id}/analyze",
    response_model=ForensicAnalysisBundle,
    dependencies=[Depends(enforce_max_body_size)],
)
def analyze_investigation_payload(
    investigation_id: str,
    case: InvestigationCase,
    store: InMemoryInvestigationStore = Depends(get_store),
    engine: ForensicEngine = Depends(get_engine),
) -> ForensicAnalysisBundle:
    """Ingest a normalized InvestigationCase from Role 1 and compute/cache forensic outputs."""
    if case.investigation_id != investigation_id:
        raise HTTPException(
            status_code=400,
            detail="Path investigation_id does not match payload investigation_id.",
        )
    try:
        store.save_case(case)
    except CaseConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    bundle = store.get_or_compute_analysis(investigation_id, engine)
    if bundle is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to compute forensic analysis.",
        )
    return bundle


@router.post(
    "/forensics/cross-case",
    response_model=CrossCaseAnalysisResponse,
    dependencies=[Depends(enforce_max_body_size)],
)
def run_cross_case_analysis(
    payload: CrossCaseRequest,
    store: InMemoryInvestigationStore = Depends(get_store),
    engine: ForensicEngine = Depends(get_engine),
) -> CrossCaseAnalysisResponse:
    """Compare multiple investigation graphs for shared infrastructure and overlapping paths."""
    cases = list(payload.cases)
    for cid in payload.case_ids:
        found = store.get_case(cid)
        if found is None:
            raise HTTPException(status_code=404, detail=f"Investigation '{cid}' not found.")
        cases.append(found)
    if len(cases) < 2:
        raise HTTPException(
            status_code=400,
            detail="Cross-case analysis requires at least 2 investigations.",
        )
    if len(cases) > MAX_CROSS_CASE_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Cross-case analysis is limited to at most {MAX_CROSS_CASE_COUNT} cases.",
        )
    return engine.analyze_cross_case(cases)


@router.get(
    "/forensics/ml-evaluation",
    response_model=MLEvaluationReport,
)
def get_ml_evaluation_report(
    engine: ForensicEngine = Depends(get_engine),
) -> MLEvaluationReport:
    """Return reproducible ML evaluation metrics on clearly labelled synthetic demo data."""
    features, labels, archetypes = generate_synthetic_ml_dataset(
        n_samples=240, random_state=engine.config.ml.random_state
    )
    return evaluate_ml_models(features, labels, archetypes, engine.config.ml)

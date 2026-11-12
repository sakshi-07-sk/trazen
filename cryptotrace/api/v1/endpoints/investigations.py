"""Investigation and forensics analysis API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from cryptotrace.api.deps import get_investigation_service
from cryptotrace.schemas.contracts import (
    InvestigationAnalyzeRequest,
    InvestigationAnalyzeResponse,
    InvestigationCreate,
    InvestigationResponse,
    PaginatedResponse,
    TransactionGraph,
    TransactionSummary,
)
from cryptotrace.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Forensic Investigation",
    description="Initiates a blockchain forensic investigation, triggers multi-hop network ingestion, and builds the initial transaction graph.",
)
async def create_investigation(
    payload: InvestigationCreate,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    inv_response, _ = await service.create_and_execute(payload)
    return inv_response


@router.get(
    "/{id}",
    response_model=InvestigationResponse,
    summary="Get Investigation Details",
    description="Fetches metadata, status, and transaction/node counts for an existing investigation.",
)
async def get_investigation(
    id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    return await service.get_investigation(id)


@router.get(
    "/{id}/graph",
    response_model=TransactionGraph,
    summary="Get Investigation Transaction Graph",
    description="Returns the multi-hop directed transaction graph (nodes, edges, evidence citations) for visualization and forensics.",
)
async def get_investigation_graph(
    id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> TransactionGraph:
    return await service.get_graph(id)


@router.get(
    "/{id}/transactions",
    response_model=PaginatedResponse[TransactionSummary],
    summary="Get Ingested Transactions",
    description="Lists all normalized canonical transactions ingested for this case with pagination and asset filtering.",
)
async def get_investigation_transactions(
    id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    asset_symbol: Optional[str] = Query(default=None, description="Filter by asset symbol (e.g. BTC, ETH, USDT)"),
    service: InvestigationService = Depends(get_investigation_service),
) -> PaginatedResponse[TransactionSummary]:
    return await service.get_transactions(
        investigation_id=id,
        page=page,
        page_size=page_size,
        asset_symbol=asset_symbol,
    )


@router.post(
    "/{id}/analyze",
    response_model=InvestigationAnalyzeResponse,
    summary="Trigger Graph Re-Analysis & Flow Accounting",
    description="Executes custom multi-hop traversal with adjusted filters (depth, min/max volume, date range) and generates full inflow/outflow metrics.",
)
async def analyze_investigation(
    id: str,
    payload: InvestigationAnalyzeRequest,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationAnalyzeResponse:
    return await service.analyze(investigation_id=id, req=payload)

"""Investigation Service handling case life cycle, analysis, and queries."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.core.exceptions import InvestigationNotFoundError
from cryptotrace.core.logging import logger
from cryptotrace.db.models.investigation import InvestigationModel
from cryptotrace.db.repository import (
    GraphRepository,
    InvestigationRepository,
    TransactionRepository,
)
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.graph.traversal import MultiHopTraversalEngine
from cryptotrace.normalization.pipeline import NormalizationPipeline
from cryptotrace.schemas.common import BlockchainType, EdgeType, TransactionStatus
from cryptotrace.schemas.contracts import (
    FlowAnalysis,
    FlowMetric,
    InvestigationAnalyzeRequest,
    InvestigationAnalyzeResponse,
    InvestigationCreate,
    InvestigationResponse,
    MultiHopTraversalRequest,
    MultiHopTraversalResult,
    PaginatedResponse,
    TransactionGraph,
    TransactionSummary,
)
from cryptotrace.schemas.audit import AuditEventCreate
from cryptotrace.services.audit.audit_service import AuditService
from cryptotrace.services.ingestion_service import IngestionService


class InvestigationService:
    """Coordinates forensic case workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.inv_repo = InvestigationRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.graph_repo = GraphRepository(session)
        self.ingestion_svc = IngestionService(session)
        self.audit_svc = AuditService(session)

    async def create_and_execute(
        self, payload: InvestigationCreate
    ) -> Tuple[InvestigationResponse, MultiHopTraversalResult]:
        """Create a new investigation, ingest multi-hop transaction network, and build graph."""
        # 1. Create DB record
        inv = await self.inv_repo.create(payload)
        await self.audit_svc.record_event(
            AuditEventCreate(
                investigation_id=inv.id,
                event_type="INVESTIGATION_CREATED",
                payload={
                    "title": payload.title,
                    "blockchain": payload.blockchain.value,
                    "target_address": payload.target_address,
                    "max_hops": payload.max_hops,
                },
            ),
            actor_override="cryptotrace-engine",
            actor_role_override="service",
        )

        try:
            await self.inv_repo.update_status(inv.id, status="ingesting")

            # 2. Ingest Multi-hop network
            engine, canonical_txs = await self.ingestion_svc.ingest_multihop_network(
                blockchain=payload.blockchain,
                seed_address=payload.target_address,
                investigation_id=inv.id,
                max_hops=payload.max_hops,
            )

            # 3. Perform Multi-hop Traversal and Flow Analysis
            traversal_engine = MultiHopTraversalEngine(engine)
            trav_req = MultiHopTraversalRequest(
                start_address=payload.target_address,
                blockchain=payload.blockchain,
                max_hops=payload.max_hops,
                min_amount=payload.min_amount,
                max_amount=payload.max_amount,
                start_time=payload.start_time,
                end_time=payload.end_time,
                include_heuristics=True,
            )
            trav_result = traversal_engine.traverse(trav_req)

            # 4. Persist Graph models
            node_models, edge_models, path_models = traversal_engine.to_db_models(
                investigation_id=inv.id,
                graph=trav_result.graph,
                paths=trav_result.paths_found,
            )
            await self.graph_repo.save_graph(
                investigation_id=inv.id,
                nodes=node_models,
                edges=edge_models,
                paths=path_models,
            )

            # 5. Mark Completed
            inv = await self.inv_repo.update_status(
                investigation_id=inv.id,
                status="completed",
                total_transactions=len(canonical_txs),
                total_nodes=trav_result.graph.node_count,
                total_edges=trav_result.graph.edge_count,
            )
            await self.audit_svc.record_event(
                AuditEventCreate(
                    investigation_id=inv.id,
                    event_type="INVESTIGATION_COMPLETED",
                    payload={
                        "total_transactions_ingested": len(canonical_txs),
                        "total_nodes": trav_result.graph.node_count,
                        "total_edges": trav_result.graph.edge_count,
                    },
                ),
                actor_override="cryptotrace-engine",
                actor_role_override="service",
            )

            response = self._to_response(inv)
            return response, trav_result

        except Exception as exc:
            logger.error(f"Investigation execution failed: {exc}", exc_info=True)
            await self.inv_repo.update_status(
                investigation_id=inv.id,
                status="failed",
                error_message=str(exc),
            )
            raise

    async def get_investigation(self, investigation_id: str) -> InvestigationResponse:
        """Fetch investigation summary by ID."""
        inv = await self.inv_repo.get_by_id(investigation_id)
        if not inv:
            raise InvestigationNotFoundError(investigation_id)
        return self._to_response(inv)

    async def get_graph(self, investigation_id: str) -> TransactionGraph:
        """Retrieve graph representation for an investigation."""
        inv = await self.inv_repo.get_by_id(investigation_id)
        if not inv:
            raise InvestigationNotFoundError(investigation_id)

        node_models, edge_models = await self.graph_repo.get_graph(investigation_id)

        # Build in-memory graph
        engine = BlockchainGraphEngine()
        for nm in node_models:
            engine.add_node(
                node_id=nm.node_id,
                node_type=nm.node_type,
                label=nm.label,
                blockchain=BlockchainType(nm.blockchain),
                chain_id=nm.chain_id,
                properties=nm.properties,
            )
        for em in edge_models:
            engine.add_edge(
                edge_id=em.id,
                source=em.source_id,
                target=em.target_id,
                edge_type=EdgeType(em.edge_type),  # cast string stored in DB → EdgeType enum
                amount=em.amount,
                asset_symbol=em.asset_symbol,
                tx_hash=em.tx_hash,
                evidence_reference=em.evidence_reference,
                is_confirmed=em.is_confirmed,
                is_heuristic=em.is_heuristic,
                properties=em.properties,
            )

        trav_engine = MultiHopTraversalEngine(engine)
        req = MultiHopTraversalRequest(
            start_address=inv.target_address,
            blockchain=BlockchainType(inv.blockchain),
            max_hops=inv.max_hops,
            include_heuristics=True,
        )
        result = trav_engine.traverse(req)
        return result.graph

    async def get_transactions(
        self,
        investigation_id: str,
        page: int = 1,
        page_size: int = 50,
        asset_symbol: Optional[str] = None,
    ) -> PaginatedResponse[TransactionSummary]:
        """Fetch paginated transactions associated with an investigation."""
        inv = await self.inv_repo.get_by_id(investigation_id)
        if not inv:
            raise InvestigationNotFoundError(investigation_id)

        tx_models, total = await self.tx_repo.list_for_investigation(
            investigation_id=investigation_id,
            page=page,
            page_size=page_size,
            asset_symbol=asset_symbol,
        )

        summaries = [
            TransactionSummary(
                chain_id=m.chain_id,
                blockchain=BlockchainType(m.blockchain),
                tx_hash=m.tx_hash,
                block_number=m.block_number,
                timestamp=m.timestamp,
                senders=m.sender_references,
                recipients=m.recipient_references,
                asset_symbol=m.asset_symbol,
                amount=m.amount,
                fee=m.fee,
                status=TransactionStatus(m.status),
                confirmations=m.confirmations,
                is_fixture=m.is_fixture,
            )
            for m in tx_models
        ]

        has_more = (page * page_size) < total
        return PaginatedResponse[TransactionSummary](
            items=summaries,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def analyze(
        self, investigation_id: str, req: InvestigationAnalyzeRequest
    ) -> InvestigationAnalyzeResponse:
        """Trigger on-demand multi-hop re-analysis with custom filters."""
        start_t = time.perf_counter()
        inv = await self.inv_repo.get_by_id(investigation_id)
        if not inv:
            raise InvestigationNotFoundError(investigation_id)

        # Ingest and rebuild graph with specified hops
        hops = req.max_hops or inv.max_hops
        engine, canonical_txs = await self.ingestion_svc.ingest_multihop_network(
            blockchain=BlockchainType(inv.blockchain),
            seed_address=inv.target_address,
            investigation_id=inv.id,
            max_hops=hops,
        )

        traversal_engine = MultiHopTraversalEngine(engine)
        trav_req = MultiHopTraversalRequest(
            start_address=inv.target_address,
            blockchain=BlockchainType(inv.blockchain),
            max_hops=hops,
            min_amount=req.min_amount,
            max_amount=req.max_amount,
            start_time=req.start_time,
            end_time=req.end_time,
            include_heuristics=req.include_heuristics,
        )
        res = traversal_engine.traverse(trav_req)

        await self.audit_svc.record_event(
            AuditEventCreate(
                investigation_id=inv.id,
                event_type="INVESTIGATION_ANALYZED",
                payload={
                    "max_hops": hops,
                    "nodes_discovered": res.graph.node_count,
                    "edges_discovered": res.graph.edge_count,
                    "include_heuristics": req.include_heuristics,
                },
            ),
            actor_override="cryptotrace-engine",
            actor_role_override="service",
        )

        execution_ms = (time.perf_counter() - start_t) * 1000.0

        return InvestigationAnalyzeResponse(
            investigation_id=inv.id,
            status="completed",
            nodes_discovered=res.graph.node_count,
            edges_discovered=res.graph.edge_count,
            flow_analysis=res.flow_analysis or FlowAnalysis(
                target_address=inv.target_address,
                blockchain=BlockchainType(inv.blockchain),
                overall_metrics=FlowMetric(),
            ),
            execution_time_ms=round(execution_ms, 2),
            analyzed_at=res.graph.generated_at,
        )

    def _to_response(self, model: InvestigationModel) -> InvestigationResponse:
        return InvestigationResponse(
            id=model.id,
            title=model.title,
            description=model.description,
            blockchain=BlockchainType(model.blockchain),
            target_address=model.target_address,
            max_hops=model.max_hops,
            status=model.status,
            total_transactions_ingested=model.total_transactions_ingested,
            total_nodes=model.total_nodes,
            total_edges=model.total_edges,
            created_at=model.created_at,
            updated_at=model.updated_at,
            parameters=model.parameters,
        )

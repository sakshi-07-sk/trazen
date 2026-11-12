"""Modular security analysis orchestrator for Role 1 investigations and future Role 2 consumers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cryptotrace.core.exceptions import InvestigationNotFoundError
from cryptotrace.db.models.transaction import TransactionModel
from cryptotrace.db.repository import GraphRepository, InvestigationRepository
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.graph.traversal import MultiHopTraversalEngine
from cryptotrace.schemas.common import BlockchainType, EdgeType
from cryptotrace.schemas.findings import SecurityFinding, SharedFindingAdapter
from cryptotrace.schemas.graph import MultiHopTraversalRequest
from cryptotrace.schemas.security_inputs import TokenMetadataInput, TransactionRecord
from cryptotrace.services.security.adapters import (
    graph_edge_to_security_input,
    graph_node_to_security_input,
    orm_tx_to_security_records,
    orm_tx_to_token_inputs,
    transaction_graph_to_security_inputs,
)
from cryptotrace.services.security.address_poisoning import AddressPoisoningDetector
from cryptotrace.services.security.blockchain_validator import (
    BlockchainDataValidator,
    BlockchainValidationReport,
)
from cryptotrace.services.security.dusting_detector import DustingDetector
from cryptotrace.services.security.graph_integrity import (
    GraphIntegrityAnalyzer,
    GraphIntegritySummary,
)
from cryptotrace.services.security.token_impersonation import TokenImpersonationDetector


class SecurityOrchestrator:
    """Runs Role 3 validation, threat detection, and graph integrity on persisted investigations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.inv_repo = InvestigationRepository(session)
        self.graph_repo = GraphRepository(session)
        self.poisoning_detector = AddressPoisoningDetector()
        self.dusting_detector = DustingDetector()
        self.token_detector = TokenImpersonationDetector()
        self.graph_analyzer = GraphIntegrityAnalyzer()
        self.tx_validator = BlockchainDataValidator()

    async def scan_investigation(
        self,
        investigation_id: str,
        *,
        include_validation_findings: bool = False,
    ) -> dict[str, Any]:
        """Run all Role 3 detectors and graph integrity checks over a persisted investigation."""
        inv = await self.inv_repo.get_by_id(investigation_id)
        if not inv:
            raise InvestigationNotFoundError(investigation_id)

        tx_stmt = (
            select(TransactionModel)
            .where(TransactionModel.investigation_id == investigation_id)
            .options(
                selectinload(TransactionModel.utxos),
                selectinload(TransactionModel.token_transfers),
            )
        )
        tx_models = list((await self.session.execute(tx_stmt)).scalars().all())

        node_models, edge_models = await self.graph_repo.get_graph(investigation_id)
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
                edge_type=EdgeType(em.edge_type),
                amount=em.amount,
                asset_symbol=em.asset_symbol,
                tx_hash=em.tx_hash,
                evidence_reference=em.evidence_reference,
                is_confirmed=em.is_confirmed,
                is_heuristic=em.is_heuristic,
                properties=em.properties,
            )

        trav_engine = MultiHopTraversalEngine(engine)
        trav_res = trav_engine.traverse(
            MultiHopTraversalRequest(
                start_address=inv.target_address,
                blockchain=BlockchainType(inv.blockchain),
                max_hops=inv.max_hops,
                include_heuristics=True,
            )
        )

        tx_records: list[TransactionRecord] = []
        token_inputs: list[TokenMetadataInput] = []
        for m in tx_models:
            tx_records.extend(orm_tx_to_security_records(m))
            token_inputs.extend(orm_tx_to_token_inputs(m))

        sec_nodes, sec_edges = transaction_graph_to_security_inputs(trav_res.graph)
        # Fallback to raw persisted graph nodes/edges if traversal was empty
        if not sec_nodes and node_models:
            sec_nodes = [
                graph_node_to_security_input(n)
                for n in trav_res.graph.nodes
            ]
        if not sec_edges and edge_models:
            sec_edges = [
                graph_edge_to_security_input(e, chain=inv.blockchain)
                for e in trav_res.graph.edges
            ]

        findings: list[SecurityFinding] = []
        findings.extend(
            self.poisoning_detector.analyze(
                investigation_id=investigation_id,
                target_wallet=inv.target_address,
                chain=inv.blockchain,
                transactions=tx_records,
            )
        )
        findings.extend(
            self.dusting_detector.analyze(
                investigation_id=investigation_id,
                transactions=tx_records,
            )
        )
        for tok in token_inputs:
            findings.extend(
                self.token_detector.analyze(investigation_id=investigation_id, token=tok)
            )

        graph_summary: GraphIntegritySummary
        graph_summary, graph_findings = self.graph_analyzer.analyze(
            investigation_id=investigation_id,
            nodes=sec_nodes,
            edges=sec_edges,
            evidence_transactions=tx_records,
        )
        findings.extend(graph_findings)

        validation_reports: list[BlockchainValidationReport] = self.tx_validator.validate_batch(
            investigation_id=investigation_id,
            transactions=tx_records,
        )
        if include_validation_findings:
            for rep in validation_reports:
                findings.extend(rep.findings)

        return {
            "investigation_id": investigation_id,
            "target_address": inv.target_address,
            "blockchain": inv.blockchain,
            "transactions_evaluated": len(tx_records),
            "tokens_evaluated": len(token_inputs),
            "graph_integrity": graph_summary,
            "validation_summary": {
                "total": len(validation_reports),
                "valid": sum(1 for r in validation_reports if r.validation_status.value == "VALID"),
                "invalid": sum(1 for r in validation_reports if r.validation_status.value == "INVALID"),
                "conflicting": sum(1 for r in validation_reports if r.validation_status.value == "CONFLICTING"),
                "incomplete": sum(1 for r in validation_reports if r.validation_status.value == "INCOMPLETE"),
            },
            "findings": findings,
            "shared_findings": [SharedFindingAdapter.to_shared_finding_dict(f) for f in findings],
        }


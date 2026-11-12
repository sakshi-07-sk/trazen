"""Async Repository Layer with Pagination and Query Optimization."""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cryptotrace.db.models.graph import GraphEdgeModel, GraphNodeModel, InvestigationPathModel
from cryptotrace.db.models.investigation import InvestigationModel
from cryptotrace.db.models.provenance import ProvenanceModel
from cryptotrace.db.models.token_transfer import TokenTransferModel
from cryptotrace.db.models.transaction import TransactionModel
from cryptotrace.db.models.utxo import UTXOModel
from cryptotrace.db.models.wallet import WalletModel
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.investigation import InvestigationCreate


class InvestigationRepository:
    """Repository managing investigation entity lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: InvestigationCreate) -> InvestigationModel:
        """Create a new investigation case."""
        investigation = InvestigationModel(
            title=payload.title,
            description=payload.description,
            blockchain=payload.blockchain.value,
            target_address=payload.target_address,
            max_hops=payload.max_hops,
            status="created",
            parameters={
                "min_amount": str(payload.min_amount) if payload.min_amount is not None else None,
                "max_amount": str(payload.max_amount) if payload.max_amount is not None else None,
                "start_time": payload.start_time.isoformat() if payload.start_time else None,
                "end_time": payload.end_time.isoformat() if payload.end_time else None,
                "tags": payload.tags,
            },
        )
        self.session.add(investigation)
        await self.session.flush()
        return investigation

    async def get_by_id(self, investigation_id: str) -> Optional[InvestigationModel]:
        """Fetch investigation by ID."""
        stmt = select(InvestigationModel).where(InvestigationModel.id == investigation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        investigation_id: str,
        status: str,
        error_message: Optional[str] = None,
        total_transactions: Optional[int] = None,
        total_nodes: Optional[int] = None,
        total_edges: Optional[int] = None,
    ) -> Optional[InvestigationModel]:
        """Update status and statistics for an investigation."""
        investigation = await self.get_by_id(investigation_id)
        if not investigation:
            return None
        investigation.status = status
        if error_message is not None:
            investigation.error_message = error_message
        if total_transactions is not None:
            investigation.total_transactions_ingested = total_transactions
        if total_nodes is not None:
            investigation.total_nodes = total_nodes
        if total_edges is not None:
            investigation.total_edges = total_edges
        await self.session.flush()
        return investigation

    async def list_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> Tuple[List[InvestigationModel], int]:
        """Return paginated investigations list."""
        offset = (page - 1) * page_size
        total_stmt = select(func.count(InvestigationModel.id))
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(InvestigationModel)
            .order_by(desc(InvestigationModel.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total


class TransactionRepository:
    """Repository managing transactions, UTXOs and Token transfers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_hash(self, blockchain: str, tx_hash: str) -> Optional[TransactionModel]:
        """Lookup transaction by blockchain and tx_hash."""
        stmt = (
            select(TransactionModel)
            .where(
                TransactionModel.blockchain == blockchain,
                TransactionModel.tx_hash == tx_hash,
            )
            .options(
                selectinload(TransactionModel.utxos),
                selectinload(TransactionModel.token_transfers),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, blockchain: str, tx_hash: str) -> bool:
        """Check duplicate transaction existence."""
        stmt = (
            select(func.count(TransactionModel.id))
            .where(
                TransactionModel.blockchain == blockchain,
                TransactionModel.tx_hash == tx_hash,
            )
        )
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def save_transaction(self, tx_model: TransactionModel) -> TransactionModel:
        """Persist canonical transaction with its UTXOs or token transfers."""
        self.session.add(tx_model)
        await self.session.flush()
        return tx_model

    async def list_for_investigation(
        self,
        investigation_id: str,
        page: int = 1,
        page_size: int = 50,
        asset_symbol: Optional[str] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
    ) -> Tuple[List[TransactionModel], int]:
        """Fetch paginated transactions for an investigation with filters."""
        stmt = select(TransactionModel).where(TransactionModel.investigation_id == investigation_id)
        if asset_symbol:
            stmt = stmt.where(TransactionModel.asset_symbol == asset_symbol)
        if min_amount is not None:
            stmt = stmt.where(TransactionModel.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(TransactionModel.amount <= max_amount)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        paged_stmt = (
            stmt.order_by(desc(TransactionModel.timestamp))
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(TransactionModel.utxos),
                selectinload(TransactionModel.token_transfers),
            )
        )
        result = await self.session.execute(paged_stmt)
        return list(result.scalars().all()), total


class GraphRepository:
    """Repository for graph nodes, edges and investigation paths."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_graph(
        self,
        investigation_id: str,
        nodes: List[GraphNodeModel],
        edges: List[GraphEdgeModel],
        paths: Optional[List[InvestigationPathModel]] = None,
    ) -> None:
        """Persist graph structure for investigation."""
        for node in nodes:
            self.session.add(node)
        for edge in edges:
            self.session.add(edge)
        if paths:
            for path in paths:
                self.session.add(path)
        await self.session.flush()

    async def get_graph(
        self, investigation_id: str
    ) -> Tuple[List[GraphNodeModel], List[GraphEdgeModel]]:
        """Retrieve persisted nodes and edges for an investigation."""
        node_stmt = select(GraphNodeModel).where(GraphNodeModel.investigation_id == investigation_id)
        edge_stmt = select(GraphEdgeModel).where(GraphEdgeModel.investigation_id == investigation_id)

        node_res = await self.session.execute(node_stmt)
        edge_res = await self.session.execute(edge_stmt)

        return list(node_res.scalars().all()), list(edge_res.scalars().all())


class ProvenanceRepository:
    """Repository for auditing data origin and payload integrity."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_provenance(self, prov: ProvenanceModel) -> ProvenanceModel:
        """Store provenance audit entry."""
        self.session.add(prov)
        await self.session.flush()
        return prov

    async def get_by_identifier(
        self, record_type: str, record_identifier: str
    ) -> Optional[ProvenanceModel]:
        """Fetch latest provenance for record."""
        stmt = (
            select(ProvenanceModel)
            .where(
                ProvenanceModel.record_type == record_type,
                ProvenanceModel.record_identifier == record_identifier,
            )
            .order_by(desc(ProvenanceModel.retrieved_at))
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


class WalletRepository:
    """Repository managing wallet entities and upserts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_blockchain_address(
        self, blockchain: str, address: str
    ) -> Optional[WalletModel]:
        """Fetch wallet by blockchain and address."""
        stmt = select(WalletModel).where(
            WalletModel.blockchain == blockchain,
            WalletModel.address == address,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert_wallet(
        self,
        address: str,
        blockchain: str,
        chain_id: str,
        balance_native: Decimal,
        transaction_count: int,
    ) -> WalletModel:
        """Upsert wallet record preventing duplicates."""
        existing = await self.get_by_blockchain_address(blockchain, address)
        if existing:
            existing.balance_native = balance_native
            existing.transaction_count = transaction_count
            await self.session.flush()
            return existing
        else:
            wallet = WalletModel(
                address=address,
                blockchain=blockchain,
                chain_id=chain_id,
                balance_native=balance_native,
                transaction_count=transaction_count,
            )
            self.session.add(wallet)
            await self.session.flush()
            return wallet

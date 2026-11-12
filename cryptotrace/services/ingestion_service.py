"""Ingestion Service coordinating connectors, normalization, and graph construction."""

import asyncio
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.connectors.base import BaseBlockchainAdapter
from cryptotrace.connectors.bitcoin.adapter import BitcoinAdapter
from cryptotrace.connectors.ethereum.adapter import EthereumAdapter
from cryptotrace.core.logging import logger
from cryptotrace.db.models.wallet import WalletModel
from cryptotrace.db.repository import ProvenanceRepository, TransactionRepository, WalletRepository
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.normalization.pipeline import NormalizationPipeline
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.transaction import CanonicalTransaction


class IngestionService:
    """Orchestrates multi-hop data ingestion and normalization."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tx_repo = TransactionRepository(session)
        self.prov_repo = ProvenanceRepository(session)
        self.wallet_repo = WalletRepository(session)
        self.btc_adapter = BitcoinAdapter()
        self.eth_adapter = EthereumAdapter()

    def _get_adapter(self, blockchain: BlockchainType) -> BaseBlockchainAdapter:
        if blockchain == BlockchainType.BITCOIN:
            return self.btc_adapter
        elif blockchain == BlockchainType.ETHEREUM:
            return self.eth_adapter
        raise ValueError(f"Unsupported blockchain: {blockchain}")

    async def ingest_address_activity(
        self,
        blockchain: BlockchainType,
        address: str,
        investigation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[CanonicalTransaction]:
        """Fetch, normalize, deduplicate, and persist transaction activity for an address."""
        adapter = self._get_adapter(blockchain)
        raw_txs = await adapter.get_transactions_for_address(address, limit=limit)

        normalized_txs: List[CanonicalTransaction] = []
        for raw in raw_txs:
            try:
                canonical = NormalizationPipeline.normalize_transaction(
                    blockchain=blockchain,
                    raw_payload=raw,
                    provider_name=adapter.provider_name,
                )

                # Deduplication check
                exists = await self.tx_repo.exists(blockchain.value, canonical.tx_hash)
                if not exists:
                    tx_model, prov_model = NormalizationPipeline.to_orm(
                        canonical, investigation_id=investigation_id
                    )
                    await self.tx_repo.save_transaction(tx_model)
                    await self.prov_repo.save_provenance(prov_model)

                normalized_txs.append(canonical)
            except Exception as e:
                logger.error(f"Error normalizing transaction payload: {e}")

        # Update or record wallet summary
        try:
            addr_info = await adapter.get_address_info(address)
            balance = Decimal("0")
            if blockchain == BlockchainType.BITCOIN:
                chain_stats = addr_info.get("chain_stats", {})
                funded = Decimal(str(chain_stats.get("funded_txo_sum", 0)))
                spent = Decimal(str(chain_stats.get("spent_txo_sum", 0)))
                balance = (funded - spent) / Decimal("100000000")
            elif blockchain == BlockchainType.ETHEREUM:
                val_wei = Decimal(str(addr_info.get("balance_wei", "0")))
                balance = val_wei / Decimal("1000000000000000000")

            clean_addr = address.lower() if blockchain == BlockchainType.ETHEREUM else address
            await self.wallet_repo.upsert_wallet(
                address=clean_addr,
                blockchain=blockchain.value,
                chain_id="btc-mainnet" if blockchain == BlockchainType.BITCOIN else "1",
                balance_native=balance,
                transaction_count=len(normalized_txs),
            )
        except Exception as e:
            logger.debug(f"Wallet summary record skipped: {e}")

        return normalized_txs

    async def ingest_multihop_network(
        self,
        blockchain: BlockchainType,
        seed_address: str,
        investigation_id: str,
        max_hops: int = 2,
        limit_per_node: int = 25,
    ) -> Tuple[BlockchainGraphEngine, List[CanonicalTransaction]]:
        """Recursively discover counterparties up to max_hops and build the forensic graph."""
        engine = BlockchainGraphEngine(name=f"inv_{investigation_id}")
        visited_addresses: Set[str] = set()
        current_frontier: Set[str] = {
            seed_address.lower() if blockchain == BlockchainType.ETHEREUM else seed_address
        }
        all_canonical_txs: List[CanonicalTransaction] = []
        seen_tx_hashes: Set[str] = set()

        bounded_hops = min(max(1, max_hops), 3)

        for hop in range(1, bounded_hops + 1):
            next_frontier: Set[str] = set()
            logger.info(
                f"Ingesting Hop {hop}/{bounded_hops} for investigation {investigation_id} "
                f"across {len(current_frontier)} addresses"
            )

            # Cap frontier to top 10 nodes per hop to avoid network explosion
            addresses_to_query = list(current_frontier - visited_addresses)[:10]
            if not addresses_to_query:
                break

            for addr in addresses_to_query:
                visited_addresses.add(addr)
                txs = await self.ingest_address_activity(
                    blockchain=blockchain,
                    address=addr,
                    investigation_id=investigation_id,
                    limit=limit_per_node,
                )

                for tx in txs:
                    if tx.tx_hash not in seen_tx_hashes:
                        seen_tx_hashes.add(tx.tx_hash)
                        all_canonical_txs.append(tx)
                        engine.add_canonical_transaction(tx, include_heuristics=True)

                    # Extract discovered counterparties for next hop
                    for r in tx.recipient_references:
                        if r and not r.startswith("op_return") and not r.startswith("unparsed"):
                            clean_r = r.lower() if blockchain == BlockchainType.ETHEREUM else r
                            if clean_r not in visited_addresses:
                                next_frontier.add(clean_r)

                    for s in tx.sender_references:
                        if s and s != "coinbase":
                            clean_s = s.lower() if blockchain == BlockchainType.ETHEREUM else s
                            if clean_s not in visited_addresses:
                                next_frontier.add(clean_s)

            current_frontier = next_frontier

        return engine, all_canonical_txs

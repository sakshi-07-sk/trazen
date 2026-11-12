"""NetworkX-based Blockchain Forensics Graph Engine."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from cryptotrace.core.logging import logger
from cryptotrace.schemas.common import BlockchainType, EdgeType, NodeType
from cryptotrace.schemas.graph import GraphEdge, GraphNode, TransactionGraph
from cryptotrace.schemas.transaction import CanonicalTransaction


class BlockchainGraphEngine:
    """Constructs and queries chain-aware directed forensic transaction graphs."""

    def __init__(self, name: str = "forensic_graph") -> None:
        self.name = name
        self.nx_graph: nx.MultiDiGraph = nx.MultiDiGraph()

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        blockchain: BlockchainType,
        chain_id: str,
        properties: Optional[Dict[str, Any]] = None,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
    ) -> None:
        """Add or update an entity node in the graph."""
        props = properties or {}
        if self.nx_graph.has_node(node_id):
            # Update existing node properties
            curr = self.nx_graph.nodes[node_id]
            curr["properties"].update(props)
            if first_seen and (not curr.get("first_seen") or first_seen < curr["first_seen"]):
                curr["first_seen"] = first_seen
            if last_seen and (not curr.get("last_seen") or last_seen > curr["last_seen"]):
                curr["last_seen"] = last_seen
        else:
            self.nx_graph.add_node(
                node_id,
                node_type=node_type,
                label=label,
                blockchain=blockchain,
                chain_id=chain_id,
                properties=props,
                first_seen=first_seen,
                last_seen=last_seen,
            )

    def add_edge(
        self,
        edge_id: str,
        source: str,
        target: str,
        edge_type: EdgeType,
        amount: Decimal,
        asset_symbol: str,
        tx_hash: str,
        evidence_reference: str,
        is_confirmed: bool = True,
        is_heuristic: bool = False,
        block_number: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add directed edge between nodes."""
        self.nx_graph.add_edge(
            source,
            target,
            key=edge_id,
            id=edge_id,
            source=source,
            target=target,
            edge_type=edge_type,
            is_confirmed=is_confirmed,
            is_heuristic=is_heuristic,
            amount=amount,
            asset_symbol=asset_symbol,
            tx_hash=tx_hash,
            evidence_reference=evidence_reference,
            block_number=block_number,
            timestamp=timestamp,
            properties=properties or {},
        )

    def add_canonical_transaction(
        self, tx: CanonicalTransaction, include_heuristics: bool = False
    ) -> None:
        """Incorporate canonical transaction into graph according to chain semantics."""
        if tx.blockchain == BlockchainType.BITCOIN:
            self._add_bitcoin_transaction(tx, include_heuristics=include_heuristics)
        elif tx.blockchain == BlockchainType.ETHEREUM:
            self._add_ethereum_transaction(tx)
        else:
            logger.warning(f"Unknown blockchain: {tx.blockchain}")

    def _add_bitcoin_transaction(
        self, tx: CanonicalTransaction, include_heuristics: bool = False
    ) -> None:
        """Model Bitcoin via UTXO architecture: Address -> [UTXO Input] -> Tx Node -> [UTXO Output] -> Address."""
        tx_node_id = f"tx:{tx.tx_hash}"
        # Add intermediate transaction node
        self.add_node(
            node_id=tx_node_id,
            node_type=NodeType.TRANSACTION,
            label=f"TX: {tx.tx_hash[:8]}...",
            blockchain=tx.blockchain,
            chain_id=tx.chain_id,
            properties={"fee_btc": str(tx.fee), "block_number": tx.block_number, "vsize": tx.vsize},
            first_seen=tx.timestamp,
            last_seen=tx.timestamp,
        )

        input_addresses: List[str] = []
        # Input UTXOs consumed -> directed edge to Tx Node
        for idx, vin in enumerate(tx.inputs):
            in_addr = vin.address or f"coinbase:{tx.tx_hash[:8]}"
            input_addresses.append(in_addr)

            self.add_node(
                node_id=in_addr,
                node_type=NodeType.WALLET if in_addr != "coinbase" else NodeType.SERVICE,
                label=in_addr[:10] + "..." if len(in_addr) > 14 else in_addr,
                blockchain=tx.blockchain,
                chain_id=tx.chain_id,
                first_seen=tx.timestamp,
                last_seen=tx.timestamp,
            )

            edge_id = f"{tx.tx_hash}:in:{idx}"
            self.add_edge(
                edge_id=edge_id,
                source=in_addr,
                target=tx_node_id,
                edge_type=EdgeType.UTXO_INPUT,
                amount=vin.amount_btc,
                asset_symbol="BTC",
                tx_hash=tx.tx_hash,
                evidence_reference=f"vin:{idx}:prev:{vin.prev_tx_hash}:{vin.vout}",
                is_confirmed=True,
                is_heuristic=False,
                block_number=tx.block_number,
                timestamp=tx.timestamp,
                properties={"vout": vin.vout, "amount_sats": vin.amount_sats},
            )

        # Output UTXOs created -> directed edge from Tx Node to Destination Address
        for idx, vout in enumerate(tx.outputs):
            out_addr = vout.address or f"op_return:{tx.tx_hash[:8]}:{idx}"
            self.add_node(
                node_id=out_addr,
                node_type=NodeType.WALLET if vout.address else NodeType.SERVICE,
                label=out_addr[:10] + "..." if len(out_addr) > 14 else out_addr,
                blockchain=tx.blockchain,
                chain_id=tx.chain_id,
                first_seen=tx.timestamp,
                last_seen=tx.timestamp,
            )

            edge_id = f"{tx.tx_hash}:out:{idx}"
            self.add_edge(
                edge_id=edge_id,
                source=tx_node_id,
                target=out_addr,
                edge_type=EdgeType.UTXO_OUTPUT,
                amount=vout.amount_btc,
                asset_symbol="BTC",
                tx_hash=tx.tx_hash,
                evidence_reference=f"vout:{idx}:{tx.tx_hash}",
                is_confirmed=True,
                is_heuristic=False,
                block_number=tx.block_number,
                timestamp=tx.timestamp,
                properties={"vout": idx, "script_type": vout.script_type, "amount_sats": vout.amount_sats},
            )

        # Co-spend heuristic (explicitly flagged is_heuristic=True, is_confirmed=False)
        if include_heuristics and len(set(input_addresses)) > 1:
            unique_inputs = list(set(input_addresses))
            for i in range(len(unique_inputs) - 1):
                h_edge_id = f"heuristic_cospend:{tx.tx_hash}:{i}"
                self.add_edge(
                    edge_id=h_edge_id,
                    source=unique_inputs[i],
                    target=unique_inputs[i + 1],
                    edge_type=EdgeType.HEURISTIC_CO_SPEND,
                    amount=Decimal("0"),
                    asset_symbol="BTC",
                    tx_hash=tx.tx_hash,
                    evidence_reference=f"cospend_in_{tx.tx_hash}",
                    is_confirmed=False,
                    is_heuristic=True,
                    block_number=tx.block_number,
                    timestamp=tx.timestamp,
                )

    def _add_ethereum_transaction(self, tx: CanonicalTransaction) -> None:
        """Model Ethereum via Account architecture: EOA -> [Transfer / Contract / Token] -> EOA."""
        from_addr = tx.from_address or (tx.sender_references[0] if tx.sender_references else "0x0")
        to_addr = tx.to_address or (tx.recipient_references[0] if tx.recipient_references else "0x0")

        # Sender Node
        self.add_node(
            node_id=from_addr,
            node_type=NodeType.WALLET,
            label=f"{from_addr[:8]}...",
            blockchain=tx.blockchain,
            chain_id=tx.chain_id,
            first_seen=tx.timestamp,
            last_seen=tx.timestamp,
        )

        # Recipient Node
        recipient_type = NodeType.CONTRACT if tx.is_contract_interaction else NodeType.WALLET
        self.add_node(
            node_id=to_addr,
            node_type=recipient_type,
            label=f"{to_addr[:8]}...",
            blockchain=tx.blockchain,
            chain_id=tx.chain_id,
            first_seen=tx.timestamp,
            last_seen=tx.timestamp,
        )

        # Native ETH Transfer Edge
        if tx.amount > Decimal("0") or not tx.token_transfers:
            edge_id = f"{tx.tx_hash}:native"
            edge_type = (
                EdgeType.CONFIRMED_TRANSFER
                if not tx.is_contract_interaction
                else EdgeType.CONTRACT_CALL
            )
            self.add_edge(
                edge_id=edge_id,
                source=from_addr,
                target=to_addr,
                edge_type=edge_type,
                amount=tx.amount,
                asset_symbol="ETH",
                tx_hash=tx.tx_hash,
                evidence_reference=f"eth_transfer:{tx.tx_hash}",
                is_confirmed=True,
                is_heuristic=False,
                block_number=tx.block_number,
                timestamp=tx.timestamp,
                properties={"gas_used": tx.gas_used, "gas_price_gwei": str(tx.gas_price_gwei)},
            )

        # ERC-20 Token Transfer Edges
        for idx, tt in enumerate(tx.token_transfers):
            self.add_node(
                node_id=tt.from_address,
                node_type=NodeType.WALLET,
                label=f"{tt.from_address[:8]}...",
                blockchain=tx.blockchain,
                chain_id=tx.chain_id,
                first_seen=tx.timestamp,
                last_seen=tx.timestamp,
            )
            self.add_node(
                node_id=tt.to_address,
                node_type=NodeType.WALLET,
                label=f"{tt.to_address[:8]}...",
                blockchain=tx.blockchain,
                chain_id=tx.chain_id,
                first_seen=tx.timestamp,
                last_seen=tx.timestamp,
            )

            tt_edge_id = f"{tx.tx_hash}:erc20:{idx}"
            self.add_edge(
                edge_id=tt_edge_id,
                source=tt.from_address,
                target=tt.to_address,
                edge_type=EdgeType.ERC20_TRANSFER,
                amount=tt.amount,
                asset_symbol=tt.token_symbol,
                tx_hash=tx.tx_hash,
                evidence_reference=f"erc20:{tt.token_address}:{tt.log_index}",
                is_confirmed=True,
                is_heuristic=False,
                block_number=tx.block_number,
                timestamp=tx.timestamp,
                properties={
                    "token_address": tt.token_address,
                    "token_name": tt.token_name,
                    "decimals": tt.token_decimals,
                    "raw_value": tt.raw_value,
                },
            )

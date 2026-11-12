"""Adapters bridging Role 1 canonical/ORM/graph models into Role 3 security inputs."""

from __future__ import annotations

from decimal import Decimal

from cryptotrace.db.models.transaction import TransactionModel
from cryptotrace.schemas.common import BlockchainType, EdgeType
from cryptotrace.schemas.graph import GraphEdge, GraphNode, TransactionGraph
from cryptotrace.schemas.security_inputs import (
    GraphEdgeInput,
    GraphNodeInput,
    TokenMetadataInput,
    TransactionRecord,
    TransferType,
)
from cryptotrace.schemas.transaction import CanonicalTransaction


def canonical_tx_to_security_records(tx: CanonicalTransaction) -> list[TransactionRecord]:
    """Adapt a Role 1 CanonicalTransaction into one or more Role 3 TransactionRecord objects.

    - Bitcoin UTXO transactions decompose into per-input (`Address -> tx:<hash>`) and
      per-output (`tx:<hash> -> Address`) UTXO flow records matching BlockchainGraphEngine.
    - Ethereum transactions emit native/contract transfer records (when native amount > 0
      or no token_transfers exist) plus one record per ERC-20 TokenTransfer.
    """
    chain = tx.blockchain.value
    status_str = tx.status.value
    prov_id = tx.provenance.raw_payload_hash

    if tx.blockchain == BlockchainType.BITCOIN:
        records: list[TransactionRecord] = []
        tx_node_id = f"tx:{tx.tx_hash}"

        for idx, vin in enumerate(tx.inputs):
            in_addr = vin.address or f"coinbase:{tx.tx_hash[:8]}"
            records.append(
                TransactionRecord(
                    tx_hash=tx.tx_hash,
                    chain=chain,
                    network=tx.chain_id,
                    block_number=tx.block_number,
                    block_hash=tx.block_hash,
                    timestamp=tx.timestamp,
                    confirmations=tx.confirmations,
                    status=status_str,
                    from_address=in_addr,
                    to_address=tx_node_id,
                    amount=vin.amount_btc,
                    raw_amount=str(vin.amount_sats),
                    asset_symbol="BTC",
                    decimals=8,
                    transfer_type=TransferType.UTXO,
                    source_provider=tx.provenance.provider_name,
                    provenance_id=prov_id,
                    vout=vin.vout if vin.vout is not None else idx,
                )
            )

        for idx, vout in enumerate(tx.outputs):
            out_addr = vout.address or f"op_return:{tx.tx_hash[:8]}:{idx}"
            records.append(
                TransactionRecord(
                    tx_hash=tx.tx_hash,
                    chain=chain,
                    network=tx.chain_id,
                    block_number=tx.block_number,
                    block_hash=tx.block_hash,
                    timestamp=tx.timestamp,
                    confirmations=tx.confirmations,
                    status=status_str,
                    from_address=tx_node_id,
                    to_address=out_addr,
                    amount=vout.amount_btc,
                    raw_amount=str(vout.amount_sats),
                    asset_symbol="BTC",
                    decimals=8,
                    transfer_type=TransferType.UTXO,
                    source_provider=tx.provenance.provider_name,
                    provenance_id=prov_id,
                    vout=vout.vout,
                )
            )

        if not records:
            records.append(
                TransactionRecord(
                    tx_hash=tx.tx_hash,
                    chain=chain,
                    network=tx.chain_id,
                    block_number=tx.block_number,
                    block_hash=tx.block_hash,
                    timestamp=tx.timestamp,
                    confirmations=tx.confirmations,
                    status=status_str,
                    from_address=tx.sender_references[0] if tx.sender_references else None,
                    to_address=tx.recipient_references[0] if tx.recipient_references else None,
                    amount=tx.amount,
                    asset_symbol="BTC",
                    decimals=8,
                    transfer_type=TransferType.UTXO,
                    source_provider=tx.provenance.provider_name,
                    provenance_id=prov_id,
                )
            )
        return records

    # Ethereum / EVM
    records = []
    if tx.amount > 0 or not tx.token_transfers:
        records.append(
            TransactionRecord(
                tx_hash=tx.tx_hash,
                chain=chain,
                network=tx.chain_id,
                block_number=tx.block_number,
                block_hash=tx.block_hash,
                timestamp=tx.timestamp,
                confirmations=tx.confirmations,
                status=status_str,
                from_address=tx.from_address or (tx.sender_references[0] if tx.sender_references else None),
                to_address=tx.to_address or (tx.recipient_references[0] if tx.recipient_references else None),
                amount=tx.amount,
                asset_symbol="ETH",
                decimals=18,
                transfer_type=TransferType.NATIVE,
                source_provider=tx.provenance.provider_name,
                provenance_id=prov_id,
            )
        )

    for tt in tx.token_transfers:
        records.append(
            TransactionRecord(
                tx_hash=tx.tx_hash,
                chain=chain,
                network=tx.chain_id,
                block_number=tx.block_number,
                block_hash=tx.block_hash,
                timestamp=tx.timestamp,
                confirmations=tx.confirmations,
                status=status_str,
                from_address=tt.from_address,
                to_address=tt.to_address,
                amount=tt.amount,
                raw_amount=tt.raw_value,
                asset_symbol=tt.token_symbol,
                token_contract=tt.token_address,
                decimals=tt.token_decimals,
                transfer_type=TransferType.ERC20,
                source_provider=tx.provenance.provider_name,
                provenance_id=prov_id,
                log_index=tt.log_index,
            )
        )

    return records


def canonical_tx_to_token_inputs(tx: CanonicalTransaction) -> list[TokenMetadataInput]:
    """Extract TokenMetadataInput records from ERC-20 transfers in a CanonicalTransaction."""
    seen: set[tuple[str, str, str, int]] = set()
    items: list[TokenMetadataInput] = []
    for tt in tx.token_transfers:
        key = (
            tx.blockchain.value,
            tt.token_address.lower(),
            tt.token_symbol,
            tt.token_decimals,
        )
        if key in seen:
            continue
        seen.add(key)
        items.append(
            TokenMetadataInput(
                chain=tx.blockchain.value,
                contract_address=tt.token_address,
                symbol=tt.token_symbol,
                name=tt.token_name,
                decimals=tt.token_decimals,
                source_provider=tx.provenance.provider_name,
            )
        )
    return items


def orm_tx_to_security_records(tx: TransactionModel) -> list[TransactionRecord]:
    """Adapt a persisted Role 1 TransactionModel (with utxos / token_transfers) to Role 3 records."""
    if tx.blockchain == BlockchainType.BITCOIN.value:
        tx_node_id = f"tx:{tx.tx_hash}"
        records: list[TransactionRecord] = []

        # Reconstruct input UTXO edges from sender_references & raw/utxo semantics.
        # Note: Role 1 stores output UTXOs in tx.utxos; input UTXO amounts aren't stored separately in DB,
        # so input-side TransactionRecord leaves amount=None unless provided, avoiding false amount mismatches.
        for addr in tx.sender_references:
            records.append(
                TransactionRecord(
                    tx_hash=tx.tx_hash,
                    chain=tx.blockchain,
                    network=tx.chain_id,
                    block_number=tx.block_number,
                    block_hash=tx.block_hash,
                    timestamp=tx.timestamp,
                    confirmations=tx.confirmations,
                    status=tx.status,
                    from_address=addr,
                    to_address=tx_node_id,
                    amount=None,
                    asset_symbol="BTC",
                    decimals=8,
                    transfer_type=TransferType.UTXO,
                    source_provider=tx.provider_name,
                    provenance_id=tx.raw_payload_hash,
                )
            )

        for utxo in tx.utxos:
            out_addr = utxo.address or f"op_return:{tx.tx_hash[:8]}:{utxo.vout}"
            records.append(
                TransactionRecord(
                    tx_hash=tx.tx_hash,
                    chain=tx.blockchain,
                    network=tx.chain_id,
                    block_number=tx.block_number,
                    block_hash=tx.block_hash,
                    timestamp=tx.timestamp,
                    confirmations=tx.confirmations,
                    status=tx.status,
                    from_address=tx_node_id,
                    to_address=out_addr,
                    amount=utxo.amount_btc,
                    raw_amount=str(utxo.amount_sats),
                    asset_symbol="BTC",
                    decimals=8,
                    transfer_type=TransferType.UTXO,
                    source_provider=tx.provider_name,
                    provenance_id=tx.raw_payload_hash,
                    vout=utxo.vout,
                )
            )
        return records

    records = []
    if tx.amount > 0 or not tx.token_transfers:
        records.append(
            TransactionRecord(
                tx_hash=tx.tx_hash,
                chain=tx.blockchain,
                network=tx.chain_id,
                block_number=tx.block_number,
                block_hash=tx.block_hash,
                timestamp=tx.timestamp,
                confirmations=tx.confirmations,
                status=tx.status,
                from_address=tx.from_address or (tx.sender_references[0] if tx.sender_references else None),
                to_address=tx.to_address or (tx.recipient_references[0] if tx.recipient_references else None),
                amount=tx.amount,
                asset_symbol="ETH",
                decimals=18,
                transfer_type=TransferType.NATIVE,
                source_provider=tx.provider_name,
                provenance_id=tx.raw_payload_hash,
            )
        )

    for tt in tx.token_transfers:
        records.append(
            TransactionRecord(
                tx_hash=tx.tx_hash,
                chain=tx.blockchain,
                network=tx.chain_id,
                block_number=tx.block_number,
                block_hash=tx.block_hash,
                timestamp=tx.timestamp,
                confirmations=tx.confirmations,
                status=tx.status,
                from_address=tt.from_address,
                to_address=tt.to_address,
                amount=tt.amount,
                raw_amount=tt.raw_value,
                asset_symbol=tt.token_symbol,
                token_contract=tt.token_address,
                decimals=tt.token_decimals,
                transfer_type=TransferType.ERC20,
                source_provider=tx.provider_name,
                provenance_id=tx.raw_payload_hash,
                log_index=tt.log_index,
            )
        )

    return records


def orm_tx_to_token_inputs(tx: TransactionModel) -> list[TokenMetadataInput]:
    """Extract TokenMetadataInput items from persisted TransactionModel token_transfers."""
    seen: set[tuple[str, str, str, int]] = set()
    items: list[TokenMetadataInput] = []
    for tt in tx.token_transfers:
        key = (tx.blockchain, tt.token_address.lower(), tt.token_symbol, tt.token_decimals)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            TokenMetadataInput(
                chain=tx.blockchain,
                contract_address=tt.token_address,
                symbol=tt.token_symbol,
                name=tt.token_name,
                decimals=tt.token_decimals,
                source_provider=tx.provider_name,
            )
        )
    return items


def _parse_log_index_from_evidence_ref(evidence_ref: str) -> int | None:
    if evidence_ref.startswith("erc20:"):
        parts = evidence_ref.split(":")
        if len(parts) >= 3 and parts[2].isdigit():
            return int(parts[2])
    return None


def _parse_vout_from_edge(edge: GraphEdge) -> int | None:
    vout_prop = edge.properties.get("vout")
    if isinstance(vout_prop, int):
        return vout_prop
    if edge.evidence_reference.startswith("vout:"):
        parts = edge.evidence_reference.split(":")
        if len(parts) >= 2 and parts[1].isdigit():
            return int(parts[1])
    return None


def graph_node_to_security_input(node: GraphNode) -> GraphNodeInput:
    """Convert Role 1 GraphNode into Role 3 GraphNodeInput."""
    return GraphNodeInput(
        node_id=node.id,
        chain=node.blockchain.value,
        node_type=node.node_type.value,
        label=node.label,
        metadata=dict(node.properties),
    )


def graph_edge_to_security_input(edge: GraphEdge, chain: str) -> GraphEdgeInput:
    """Convert Role 1 GraphEdge into Role 3 GraphEdgeInput preserving UTXO & ERC-20 semantics."""
    token_contract = edge.properties.get("token_address")
    if not token_contract and edge.edge_type == EdgeType.ERC20_TRANSFER and edge.evidence_reference.startswith("erc20:"):
        parts = edge.evidence_reference.split(":")
        if len(parts) >= 2:
            token_contract = parts[1]

    # Recover exact satoshi Decimal when SQLite Numeric(38, 18) introduces float64 ulp noise (~1e-16),
    # while preserving real discrepancies (> 1e-12) so tampered DB amounts are still flagged.
    resolved_amount = edge.amount
    if chain == BlockchainType.BITCOIN.value and edge.properties.get("amount_sats") is not None:
        exact_sats_btc = Decimal(str(edge.properties["amount_sats"])) / Decimal("100000000")
        if abs(edge.amount - exact_sats_btc) <= Decimal("1e-12"):
            resolved_amount = exact_sats_btc

    return GraphEdgeInput(
        edge_id=edge.id,
        source=edge.source,
        target=edge.target,
        tx_hash=edge.tx_hash,
        chain=chain,
        edge_type=edge.edge_type.value,
        is_confirmed=edge.is_confirmed,
        is_heuristic=edge.is_heuristic,
        block_number=edge.block_number,
        asset=edge.asset_symbol,
        token_contract=token_contract,
        amount=resolved_amount,
        provenance_ref=edge.properties.get("provenance_ref"),
        log_index=_parse_log_index_from_evidence_ref(edge.evidence_reference),
        vout=_parse_vout_from_edge(edge),
        metadata={**edge.properties, "evidence_reference": edge.evidence_reference},
    )


def transaction_graph_to_security_inputs(
    graph: TransactionGraph,
) -> tuple[list[GraphNodeInput], list[GraphEdgeInput]]:
    """Convert a Role 1 TransactionGraph into Role 3 GraphNodeInput and GraphEdgeInput lists."""
    node_chain_map = {n.id: n.blockchain.value for n in graph.nodes}
    default_chain = graph.nodes[0].blockchain.value if graph.nodes else "ethereum"

    sec_nodes = [graph_node_to_security_input(n) for n in graph.nodes]
    sec_edges = [
        graph_edge_to_security_input(
            e,
            chain=node_chain_map.get(e.source) or node_chain_map.get(e.target) or default_chain,
        )
        for e in graph.edges
    ]
    return sec_nodes, sec_edges


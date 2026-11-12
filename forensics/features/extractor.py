"""Pure, cached wallet-level behavioural feature extractor (Bitcoin UTXO & Ethereum account aware)."""

from __future__ import annotations

import statistics
from typing import Dict, List

from forensics.graph.index import InvestigationGraphIndex, TransferLeg
from forensics.schemas.output import WalletFeatureVector


def _safe_median(values: List[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def _safe_mean(values: List[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _safe_cv(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    if mean <= 0:
        return 0.0
    return float(statistics.pstdev(values) / mean)


def _compute_timing_metrics(legs: List[TransferLeg]) -> tuple[float, float, float]:
    """Return (velocity_per_day, max_dormancy_seconds, timing_std_seconds)."""
    if not legs:
        return 0.0, 0.0, 0.0
    timestamps = sorted({leg.timestamp for leg in legs})
    if len(timestamps) < 2:
        return float(len(legs)), 0.0, 0.0

    deltas = [
        (timestamps[i] - timestamps[i - 1]).total_seconds() for i in range(1, len(timestamps))
    ]
    span_seconds = max(1.0, (timestamps[-1] - timestamps[0]).total_seconds())
    velocity_per_day = len(legs) / max(span_seconds / 86400.0, 1.0 / 24.0)
    max_dormancy = max(deltas) if deltas else 0.0
    timing_std = float(statistics.pstdev(deltas)) if len(deltas) >= 2 else 0.0
    return velocity_per_day, max_dormancy, timing_std


def extract_wallet_features(index: InvestigationGraphIndex, address: str) -> WalletFeatureVector:
    """Extract and cache behavioural features for a single wallet address."""
    cached = index._feature_cache.get(address)
    if isinstance(cached, WalletFeatureVector):
        return cached

    inbound = index.inbound_legs.get(address, [])
    outbound = index.outbound_legs.get(address, [])
    all_legs = inbound + outbound

    # Deduplicate by tx_id for transaction-level counts on account/UTXO
    inbound_tx_ids = {leg.tx_id for leg in inbound}
    outbound_tx_ids = {leg.tx_id for leg in outbound}
    all_tx_ids = inbound_tx_ids | outbound_tx_ids

    unique_senders = {leg.sender for leg in inbound}
    unique_receivers = {leg.receiver for leg in outbound}
    unique_counterparties = unique_senders | unique_receivers

    total_inflow = sum(leg.value for leg in inbound)
    total_outflow = sum(leg.value for leg in outbound)
    net_flow = total_inflow - total_outflow
    residual_ratio = max(0.0, net_flow / total_inflow) if total_inflow > 0 else 0.0

    values = [leg.value for leg in all_legs if leg.value > 0]
    velocity, dormancy, timing_std = _compute_timing_metrics(all_legs)

    in_count = len(inbound_tx_ids)
    out_count = len(outbound_tx_ids)
    total_count = len(all_tx_ids)

    # Fallback to graph edge counts when normalized transaction list is absent
    if total_count == 0 and address in index.nx_graph:
        in_edges = list(index.nx_graph.in_edges(address, data=True))
        out_edges = list(index.nx_graph.out_edges(address, data=True))
        in_count = sum(int(d.get("tx_count", 1)) for _, _, d in in_edges)
        out_count = sum(int(d.get("tx_count", 1)) for _, _, d in out_edges)
        total_count = in_count + out_count
        unique_senders = {u for u, _, _ in in_edges}
        unique_receivers = {v for _, v, _ in out_edges}
        unique_counterparties = unique_senders | unique_receivers
        total_inflow = sum(float(d.get("total_value", 0.0)) for _, _, d in in_edges)
        total_outflow = sum(float(d.get("total_value", 0.0)) for _, _, d in out_edges)
        net_flow = total_inflow - total_outflow
        residual_ratio = max(0.0, net_flow / total_inflow) if total_inflow > 0 else 0.0
        values = [float(d.get("total_value", 0.0)) for _, _, d in (in_edges + out_edges) if float(d.get("total_value", 0.0)) > 0]

    fan_in_ratio = (len(unique_senders) / max(1, in_count)) if in_count > 0 else 0.0
    fan_out_ratio = (len(unique_receivers) / max(1, out_count)) if out_count > 0 else 0.0

    # Service & risk exposure among counterparties and self
    labelled_counterparties = sum(
        1 for cp in unique_counterparties if index.get_labels(cp)
    )
    risk_counterparties = sum(
        1
        for cp in unique_counterparties
        if any(lbl.risk_indicator in {"high", "critical"} for lbl in index.get_labels(cp))
    )
    cp_denom = max(1, len(unique_counterparties))
    known_service_exposure = labelled_counterparties / cp_denom
    known_risk_service_exposure = risk_counterparties / cp_denom

    bridge_interactions = sum(
        1
        for leg in all_legs
        if leg.is_bridge_interaction
        or index.has_category(leg.sender, {"bridge"})
        or index.has_category(leg.receiver, {"bridge"})
    )

    # Chain-specific features: Bitcoin UTXO vs Ethereum account-based
    utxo_txs = index.utxo_txs_by_address.get(address, [])
    if utxo_txs:
        utxo_avg_inputs = statistics.fmean(len(tx.inputs) for tx in utxo_txs)
        utxo_avg_outputs = statistics.fmean(len(tx.outputs) for tx in utxo_txs)
        # Address reuse: address appears in both inputs and outputs across UTXO txs,
        # or receives outputs across multiple txs and also spends from the same address.
        in_occurrences = sum(
            1 for tx in utxo_txs if any(inp.address == address for inp in tx.inputs)
        )
        out_occurrences = sum(
            1 for tx in utxo_txs if any(out.address == address for out in tx.outputs)
        )
        self_change_occurrences = sum(
            1
            for tx in utxo_txs
            if any(inp.address == address for inp in tx.inputs)
            and any(out.address == address for out in tx.outputs)
        )
        address_reuse_count = max(0, (in_occurrences > 0 and out_occurrences > 1) * (out_occurrences - 1) + self_change_occurrences)
    else:
        utxo_avg_inputs = 0.0
        utxo_avg_outputs = 0.0
        address_reuse_count = 0

    non_utxo_legs = [leg for leg in all_legs if not leg.is_utxo]
    if non_utxo_legs:
        contract_ratio = sum(1 for leg in non_utxo_legs if leg.is_contract_call) / len(non_utxo_legs)
        token_ratio = sum(1 for leg in non_utxo_legs if leg.is_token_transfer) / len(non_utxo_legs)
    else:
        contract_ratio = 0.0
        token_ratio = 0.0

    vec = WalletFeatureVector(
        address=address,
        chain=index.chain,
        inbound_tx_count=in_count,
        outbound_tx_count=out_count,
        total_tx_count=total_count,
        unique_senders=len(unique_senders),
        unique_receivers=len(unique_receivers),
        unique_counterparties=len(unique_counterparties),
        total_inflow=round(total_inflow, 8),
        total_outflow=round(total_outflow, 8),
        net_flow=round(net_flow, 8),
        residual_balance_ratio=round(residual_ratio, 4),
        median_tx_value=round(_safe_median(values), 8),
        mean_tx_value=round(_safe_mean(values), 8),
        tx_value_cv=round(_safe_cv(values), 4),
        tx_velocity_per_day=round(velocity, 4),
        dormancy_period_seconds=round(dormancy, 2),
        fan_in_ratio=round(fan_in_ratio, 4),
        fan_out_ratio=round(fan_out_ratio, 4),
        known_service_exposure=round(known_service_exposure, 4),
        known_risk_service_exposure=round(known_risk_service_exposure, 4),
        bridge_interaction_count=bridge_interactions,
        tx_timing_variation_seconds=round(timing_std, 2),
        utxo_avg_inputs=round(utxo_avg_inputs, 4),
        utxo_avg_outputs=round(utxo_avg_outputs, 4),
        address_reuse_count=address_reuse_count,
        contract_interaction_ratio=round(contract_ratio, 4),
        token_transfer_ratio=round(token_ratio, 4),
    )
    index._feature_cache[address] = vec
    return vec


def extract_all_wallet_features(index: InvestigationGraphIndex) -> Dict[str, WalletFeatureVector]:
    """Extract and cache behavioural feature vectors for every address in the investigation."""
    return {
        addr: extract_wallet_features(index, addr)
        for addr in sorted(index.all_addresses)
    }

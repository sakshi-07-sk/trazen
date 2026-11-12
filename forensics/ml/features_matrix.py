"""Shared feature vectorization helpers for lightweight scikit-learn models."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from forensics.schemas.output import WalletFeatureVector


ML_FEATURE_NAMES: Tuple[str, ...] = (
    "inbound_tx_count",
    "outbound_tx_count",
    "unique_senders",
    "unique_receivers",
    "total_inflow",
    "total_outflow",
    "residual_balance_ratio",
    "median_tx_value",
    "tx_value_cv",
    "tx_velocity_per_day",
    "dormancy_period_seconds",
    "fan_in_ratio",
    "fan_out_ratio",
    "known_service_exposure",
    "bridge_interaction_count",
    "tx_timing_variation_seconds",
    "utxo_avg_inputs",
    "utxo_avg_outputs",
    "address_reuse_count",
    "contract_interaction_ratio",
)


def vectorize_wallet_features(
    features_by_addr: Dict[str, WalletFeatureVector],
) -> Tuple[List[str], np.ndarray]:
    """Convert wallet feature dict into deterministic sorted (addresses, 2D float array)."""
    addresses = sorted(features_by_addr.keys())
    if not addresses:
        return [], np.empty((0, len(ML_FEATURE_NAMES)), dtype=float)

    rows = [
        [float(getattr(features_by_addr[addr], name)) for name in ML_FEATURE_NAMES]
        for addr in addresses
    ]
    return addresses, np.asarray(rows, dtype=float)

"""DBSCAN behavioural wallet clustering in standardized feature space."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from forensics.config import MLConfig
from forensics.ml.features_matrix import vectorize_wallet_features
from forensics.schemas.output import WalletFeatureVector


def cluster_wallet_behaviours(
    features_by_addr: Dict[str, WalletFeatureVector],
    cfg: MLConfig,
) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """Group wallets with similar behavioural vectors via DBSCAN."""
    addresses, matrix = vectorize_wallet_features(features_by_addr)
    if not addresses:
        return {}, {"cluster_count": 0, "outlier_count": 0, "clusters": {}}

    if len(addresses) < cfg.dbscan_min_samples:
        labels = {addr: -1 for addr in addresses}
        return labels, {
            "cluster_count": 0,
            "outlier_count": len(addresses),
            "clusters": {"-1": addresses},
            "note": "Wallet count below dbscan_min_samples.",
        }

    scaled = StandardScaler().fit_transform(matrix)
    db = DBSCAN(eps=cfg.dbscan_eps, min_samples=cfg.dbscan_min_samples)
    raw_labels = db.fit_predict(scaled)

    addr_labels: Dict[str, int] = {}
    grouped: Dict[str, List[str]] = defaultdict(list)
    for addr, lbl in zip(addresses, raw_labels):
        int_lbl = int(lbl)
        addr_labels[addr] = int_lbl
        grouped[str(int_lbl)].append(addr)

    cluster_ids = [k for k in grouped.keys() if k != "-1"]
    summary = {
        "cluster_count": len(cluster_ids),
        "outlier_count": len(grouped.get("-1", [])),
        "clusters": dict(grouped),
    }
    return addr_labels, summary

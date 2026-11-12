"""Explainable Isolation Forest anomaly prioritization (not a criminality classifier)."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from forensics.config import MLConfig
from forensics.ml.features_matrix import ML_FEATURE_NAMES, vectorize_wallet_features
from forensics.schemas.output import WalletFeatureVector


def prioritize_wallet_anomalies(
    features_by_addr: Dict[str, WalletFeatureVector],
    cfg: MLConfig,
) -> Dict[str, Dict[str, Any]]:
    """Score and rank wallets by behavioural deviation using Isolation Forest.

    NOTE: Outputs reflect statistical deviation within the cohort for analyst prioritization,
    never a criminality probability.
    """
    addresses, matrix = vectorize_wallet_features(features_by_addr)
    if not addresses:
        return {}

    if len(addresses) < 4:
        return {
            addr: {
                "anomaly_score": 0.0,
                "priority_rank": idx + 1,
                "is_outlier": False,
                "top_deviating_features": [],
                "interpretation": "Insufficient cohort size (< 4 wallets) for statistical anomaly prioritization.",
            }
            for idx, addr in enumerate(addresses)
        }

    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    model = IsolationForest(
        n_estimators=100,
        contamination=cfg.isolation_forest_contamination,
        random_state=cfg.random_state,
    )
    preds = model.fit_predict(scaled)
    # decision_function: positive = inlier, negative = outlier -> invert to [0, 1]
    raw_scores = -model.decision_function(scaled)
    min_s, max_s = float(np.min(raw_scores)), float(np.max(raw_scores))
    span = max(max_s - min_s, 1e-9)
    norm_scores = [(float(s) - min_s) / span for s in raw_scores]

    # Rank descending by anomaly score
    ranked_indices = sorted(range(len(addresses)), key=lambda i: norm_scores[i], reverse=True)
    ranks = {idx: rank + 1 for rank, idx in enumerate(ranked_indices)}

    results: Dict[str, Dict[str, Any]] = {}
    for i, addr in enumerate(addresses):
        z_vec = scaled[i]
        top_idx = np.argsort(np.abs(z_vec))[::-1][:3]
        top_deviations = [
            {
                "feature": ML_FEATURE_NAMES[j],
                "z_score": round(float(z_vec[j]), 3),
                "raw_value": round(float(matrix[i, j]), 6),
            }
            for j in top_idx
            if abs(float(z_vec[j])) > 0.5
        ]
        results[addr] = {
            "anomaly_score": round(norm_scores[i], 4),
            "priority_rank": ranks[i],
            "is_outlier": bool(preds[i] == -1),
            "top_deviating_features": top_deviations,
            "interpretation": (
                "Behavioural anomaly priority score (statistical deviation only; NOT criminality probability)."
            ),
        }

    return results

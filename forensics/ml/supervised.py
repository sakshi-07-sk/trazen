"""Lightweight Random Forest classifier strictly for synthetic pattern demo evaluation."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from forensics.config import MLConfig
from forensics.ml.features_matrix import ML_FEATURE_NAMES


class SyntheticPatternClassifier:
    """Random Forest trained strictly on clearly identified synthetic behavioural data.

    IMPORTANT: Never present outputs as real-world criminality predictions.
    """

    PROVENANCE_NOTICE = (
        "SYNTHETIC_DEMO_DATA_ONLY: Trained on synthetic behavioural archetypes; "
        "scores reflect pattern similarity, not real criminality."
    )

    def __init__(self, cfg: MLConfig) -> None:
        self.cfg = cfg
        self.model = RandomForestClassifier(
            n_estimators=120,
            max_depth=6,
            class_weight="balanced",
            random_state=cfg.random_state,
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SyntheticPatternClassifier":
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("SyntheticPatternClassifier must be fitted before calling predict().")
        return self.model.predict(X)

    def predict_pattern_similarity(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("SyntheticPatternClassifier must be fitted before scoring.")
        return self.model.predict_proba(X)[:, 1]

    def top_feature_importances(self, top_k: int = 5) -> List[Tuple[str, float]]:
        if not self.is_fitted:
            return []
        pairs = list(zip(ML_FEATURE_NAMES, self.model.feature_importances_))
        pairs.sort(key=lambda item: item[1], reverse=True)
        return [(name, round(float(imp), 4)) for name, imp in pairs[:top_k]]

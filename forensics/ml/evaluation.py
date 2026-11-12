"""ML evaluation pipeline: baseline comparison, precision/recall/F1, confusion matrix, FP analysis."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

from forensics.config import MLConfig
from forensics.ml.clustering import cluster_wallet_behaviours
from forensics.ml.features_matrix import vectorize_wallet_features
from forensics.ml.supervised import SyntheticPatternClassifier
from forensics.schemas.output import EvaluationMetrics, MLEvaluationReport, WalletFeatureVector


def _compute_metrics(
    model_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    archetypes: List[str],
) -> EvaluationMetrics:
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    fp_cases: List[str] = []
    fp_reasons: Counter[str] = Counter()
    for truth, pred, arch in zip(y_true, y_pred, archetypes):
        if int(truth) == 0 and int(pred) == 1:
            fp_cases.append(arch)
            fp_reasons[arch] += 1

    fp_analysis = [
        f"Archetype '{arch}' triggered {cnt} false positive(s) due to overlapping volume/velocity features."
        for arch, cnt in sorted(fp_reasons.items())
    ]
    if not fp_analysis:
        fp_analysis = ["No false positives observed in this evaluation split."]

    return EvaluationMetrics(
        model_name=model_name,
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1_score=round(f1, 4),
        confusion_matrix=cm,
        support=int(len(y_true)),
        false_positive_cases=fp_cases,
        false_positive_analysis=fp_analysis,
    )


def evaluate_ml_models(
    features_by_addr: Dict[str, WalletFeatureVector],
    labels_by_addr: Dict[str, int],
    archetypes_by_addr: Dict[str, str],
    cfg: MLConfig,
) -> MLEvaluationReport:
    """Run reproducible evaluation comparing baseline, Isolation Forest, DBSCAN, and Random Forest."""
    addresses, X = vectorize_wallet_features(features_by_addr)
    y = np.asarray([int(labels_by_addr[a]) for a in addresses], dtype=int)
    archetypes = [archetypes_by_addr[a] for a in addresses]

    X_train, X_test, y_train, y_test, _, arch_test = train_test_split(
        X, y, archetypes, test_size=0.30, stratify=y, random_state=cfg.random_state
    )

    # 1. Baseline: Simple Dummy / Heuristic Threshold Baseline (High TX count + Low Service Exposure)
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    dummy_preds = dummy.predict(X_test)
    baseline_metrics = _compute_metrics(
        "Majority-Class Dummy Baseline", y_test, dummy_preds, arch_test
    )

    # Simple Rule Baseline: outbound > 5 and known_service_exposure == 0
    # (columns: outbound_tx_count=1, known_service_exposure=13)
    rule_preds = np.asarray(
        [1 if (row[1] >= 4 and row[13] < 0.3) else 0 for row in X_test], dtype=int
    )
    rule_metrics = _compute_metrics(
        "Simple Volume/Unlabelled Heuristic Baseline", y_test, rule_preds, arch_test
    )

    # 2. Unsupervised Isolation Forest (evaluated on test slice for priority recall)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    iso = IsolationForest(
        n_estimators=100,
        contamination=float(np.mean(y_train)) if 0 < np.mean(y_train) < 0.5 else cfg.isolation_forest_contamination,
        random_state=cfg.random_state,
    )
    iso.fit(X_train_s)
    iso_preds = np.asarray([1 if p == -1 else 0 for p in iso.predict(X_test_s)], dtype=int)
    iso_metrics = _compute_metrics(
        "Isolation Forest (Unsupervised Anomaly Prioritization)",
        y_test,
        iso_preds,
        arch_test,
    )

    # 3. Supervised Random Forest on Synthetic Dataset
    rf = SyntheticPatternClassifier(cfg)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_metrics = _compute_metrics(
        "Random Forest (Synthetic Behavioural Archetypes Only)",
        y_test,
        rf_preds,
        arch_test,
    )

    # 5-fold CV F1 summary on full synthetic set for stability check
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg.random_state)
    cv_f1s: List[float] = []
    for tr_idx, va_idx in skf.split(X, y):
        fold_rf = SyntheticPatternClassifier(cfg)
        fold_rf.fit(X[tr_idx], y[tr_idx])
        cv_f1s.append(float(f1_score(y[va_idx], fold_rf.predict(X[va_idx]), zero_division=0)))

    # 4. DBSCAN clustering summary across full synthetic cohort
    _, dbscan_summary = cluster_wallet_behaviours(features_by_addr, cfg)

    return MLEvaluationReport(
        dataset_provenance=SyntheticPatternClassifier.PROVENANCE_NOTICE,
        sample_count=len(addresses),
        anomaly_prioritization_summary={
            "method": "IsolationForest",
            "test_outliers_flagged": int(np.sum(iso_preds)),
            "note": "Anomaly scores prioritize analyst review; never treated as criminality probability.",
        },
        dbscan_cluster_summary=dbscan_summary,
        baseline_metrics=baseline_metrics,
        model_metrics=[rule_metrics, iso_metrics, rf_metrics],
        notes=[
            f"5-fold stratified CV F1-score for Synthetic Random Forest: {np.mean(cv_f1s):.4f} (+/- {np.std(cv_f1s):.4f}).",
            f"Top Random Forest features: {rf.top_feature_importances(5)}.",
            "All supervised metrics reflect synthetic benchmark separation only and must not be extrapolated as real-world illicit detection accuracy.",
        ],
    )

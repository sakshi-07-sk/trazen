"""Unit tests for Isolation Forest, DBSCAN, Synthetic Random Forest, and ML evaluation."""

from __future__ import annotations

from forensics.datasets.synthetic_ml import generate_synthetic_ml_dataset
from forensics.ml.anomaly import prioritize_wallet_anomalies
from forensics.ml.clustering import cluster_wallet_behaviours
from forensics.ml.evaluation import evaluate_ml_models
from tests.forensics_support import config  # noqa: F401


def test_ml_evaluation_report_has_baseline_metrics_confusion_matrix_and_provenance(config) -> None:
    features, labels, archetypes = generate_synthetic_ml_dataset(
        n_samples=200, random_state=config.ml.random_state
    )
    report = evaluate_ml_models(features, labels, archetypes, config.ml)

    assert "SYNTHETIC_DEMO_DATA_ONLY" in report.dataset_provenance
    assert report.sample_count >= 180
    assert report.baseline_metrics.precision >= 0.0
    assert len(report.model_metrics) == 3

    rf_metrics = [m for m in report.model_metrics if "Random Forest" in m.model_name][0]
    assert rf_metrics.f1_score >= 0.90
    assert len(rf_metrics.confusion_matrix) == 2
    assert len(rf_metrics.confusion_matrix[0]) == 2
    assert len(rf_metrics.false_positive_analysis) >= 1


def test_isolation_forest_and_dbscan_explainability(config) -> None:
    features, _, _ = generate_synthetic_ml_dataset(n_samples=80, random_state=config.ml.random_state)
    anomalies = prioritize_wallet_anomalies(features, config.ml)
    assert len(anomalies) == len(features)
    sample = next(iter(anomalies.values()))
    assert 0.0 <= sample["anomaly_score"] <= 1.0
    assert "NOT criminality probability" in sample["interpretation"]

    db_labels, db_summary = cluster_wallet_behaviours(features, config.ml)
    assert len(db_labels) == len(features)
    assert db_summary["cluster_count"] >= 1

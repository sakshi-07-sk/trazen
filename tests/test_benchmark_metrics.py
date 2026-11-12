"""Deterministic precision and recall benchmark tests across all 11 scenarios."""

from __future__ import annotations

from scripts.run_evaluation import compute_heuristic_benchmark
from forensics.engine import ForensicEngine
from tests.forensics_support import config, engine  # noqa: F401


def test_deterministic_benchmark_precision_and_recall(engine: ForensicEngine) -> None:
    report = compute_heuristic_benchmark(engine)
    assert report["scenario_count"] == 11
    assert report["false_positives"] == 0, f"Unexpected false positives: {report}"
    assert report["false_negatives"] == 0, f"Unexpected false negatives: {report}"
    assert report["precision"] == 1.0
    assert report["recall"] == 1.0
    assert report["f1_score"] == 1.0

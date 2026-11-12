"""Run deterministic forensic benchmark & synthetic ML evaluation report."""

from __future__ import annotations

import json

from forensics.datasets.fixtures import build_all_benchmark_scenarios
from forensics.datasets.synthetic_ml import generate_synthetic_ml_dataset
from forensics.engine import ForensicEngine
from forensics.ml.evaluation import evaluate_ml_models


def compute_heuristic_benchmark(engine: ForensicEngine) -> dict:
    scenarios = build_all_benchmark_scenarios()
    tp = fp = fn = tn = 0
    per_scenario = []

    for exp in scenarios:
        bundle = engine.analyze_case(exp.case)
        emitted = {f.rule_id for f in bundle.findings_response.findings}

        matched_expected = exp.expected_rule_ids & emitted
        missed_expected = exp.expected_rule_ids - emitted
        triggered_forbidden = exp.forbidden_rule_ids & emitted

        tp += len(matched_expected)
        fn += len(missed_expected)
        fp += len(triggered_forbidden)
        tn += len(exp.forbidden_rule_ids - emitted)

        per_scenario.append(
            {
                "investigation_id": exp.case.investigation_id,
                "description": exp.description,
                "expected": sorted(exp.expected_rule_ids),
                "emitted": sorted(emitted),
                "missed": sorted(missed_expected),
                "false_positives": sorted(triggered_forbidden),
                "risk_priority": bundle.risk_response.risk_priority,
                "attribution_confidence": bundle.risk_response.attribution_confidence,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "scenario_count": len(scenarios),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "scenarios": per_scenario,
    }


def main() -> None:
    engine = ForensicEngine()
    heuristic_report = compute_heuristic_benchmark(engine)
    features, labels, archetypes = generate_synthetic_ml_dataset(
        n_samples=240, random_state=engine.config.ml.random_state
    )
    ml_report = evaluate_ml_models(features, labels, archetypes, engine.config.ml)

    output = {
        "heuristic_benchmark": heuristic_report,
        "ml_evaluation": ml_report.model_dump(mode="json"),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

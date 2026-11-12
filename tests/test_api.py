"""API integration tests for FastAPI forensic endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from forensics.api.app import create_app
from forensics.datasets.fixtures import make_peel_chain_eth_case


client = TestClient(create_app())


def test_get_findings_matches_shared_output_contract() -> None:
    resp = client.get("/api/v1/investigations/CASE-PEEL-ETH-01/findings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["investigation_id"] == "CASE-PEEL-ETH-01"
    assert data["total_count"] >= 1

    finding = data["findings"][0]
    required_keys = {
        "finding_id",
        "rule_id",
        "rule_version",
        "title",
        "category",
        "severity",
        "confidence",
        "explanation",
        "evidence_refs",
        "limitations",
    }
    assert required_keys.issubset(finding.keys())
    assert finding["finding_id"].startswith("FT-")
    assert 0.0 <= finding["confidence"] <= 1.0
    assert len(finding["evidence_refs"]) >= 1
    assert len(finding["limitations"]) >= 1


def test_get_risk_returns_four_dimensions_and_ranked_receivers() -> None:
    resp = client.get("/api/v1/investigations/CASE-PEEL-ETH-01/risk")
    assert resp.status_code == 200
    data = resp.json()
    for field in (
        "risk_priority",
        "attribution_confidence",
        "known_risk_exposure",
        "investigation_coverage",
        "contributing_factors",
        "supporting_finding_ids",
        "counter_evidence",
        "confidence_limitations",
        "scoring_rule_version",
        "probable_end_receivers",
    ):
        assert field in data
    assert data["probable_end_receivers"][0]["candidate_destination"] == "0xFinalSink"


def test_post_analyze_and_cross_case_and_ml_evaluation() -> None:
    custom_case = make_peel_chain_eth_case()
    custom_case.investigation_id = "CASE-CUSTOM-API-01"
    post_resp = client.post(
        "/api/v1/investigations/CASE-CUSTOM-API-01/analyze",
        json=custom_case.model_dump(mode="json"),
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["investigation_id"] == "CASE-CUSTOM-API-01"

    cc_resp = client.post(
        "/api/v1/forensics/cross-case",
        json={"case_ids": ["CASE-CC-A", "CASE-CC-B"]},
    )
    assert cc_resp.status_code == 200
    assert len(cc_resp.json()["cross_case_findings"]) >= 1

    ml_resp = client.get("/api/v1/forensics/ml-evaluation")
    assert ml_resp.status_code == 200
    assert "SYNTHETIC_DEMO_DATA_ONLY" in ml_resp.json()["dataset_provenance"]


def test_missing_investigation_returns_404() -> None:
    resp = client.get("/api/v1/investigations/DOES-NOT-EXIST/findings")
    assert resp.status_code == 404
    resp2 = client.get("/api/v1/investigations/DOES-NOT-EXIST/risk")
    assert resp2.status_code == 404

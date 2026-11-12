"""Unit tests for cross-case relationship analysis."""

from __future__ import annotations

from forensics.datasets.fixtures import (
    make_cross_case_shared_destination_cases,
    make_normal_wallet_case,
)
from forensics.engine import ForensicEngine
from tests.forensics_support import config, engine  # noqa: F401


def test_cross_case_detects_shared_sink_and_path_while_ignoring_public_cex(
    engine: ForensicEngine,
) -> None:
    cases = make_cross_case_shared_destination_cases()
    resp = engine.analyze_cross_case(cases)

    assert "0xSharedMajorCEX" in resp.ignored_public_hubs
    rule_ids = {ccf.finding.rule_id for ccf in resp.cross_case_findings}
    assert "CROSS-CASE-DEST-01" in rule_ids
    assert "CROSS-CASE-PATH-01" in rule_ids

    dest_findings = [ccf for ccf in resp.cross_case_findings if ccf.finding.rule_id == "CROSS-CASE-DEST-01"]
    assert "0xSharedInfraSink" in dest_findings[0].common_destinations
    assert "0xSharedMajorCEX" not in dest_findings[0].common_destinations


def test_cross_case_disjoint_cases_produce_no_shared_findings(engine: ForensicEngine) -> None:
    cases = [make_normal_wallet_case(), make_cross_case_shared_destination_cases()[0]]
    resp = engine.analyze_cross_case(cases)
    assert resp.cross_case_findings == []

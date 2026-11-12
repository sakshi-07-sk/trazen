"""Unit tests for 4-dimensional risk scoring and probable end-receiver ranking."""

from __future__ import annotations

from forensics.datasets.fixtures import (
    make_incomplete_graph_case,
    make_mixer_pattern_case,
    make_normal_wallet_case,
    make_peel_chain_eth_case,
)
from forensics.engine import ForensicEngine
from tests.forensics_support import config, engine  # noqa: F401


def test_risk_dimensions_are_separate_and_explainable(engine: ForensicEngine) -> None:
    peel_bundle = engine.analyze_case(make_peel_chain_eth_case())
    normal_bundle = engine.analyze_case(make_normal_wallet_case())

    peel_risk = peel_bundle.risk_response
    normal_risk = normal_bundle.risk_response

    assert peel_risk.risk_priority > normal_risk.risk_priority
    assert peel_risk.known_risk_exposure > normal_risk.known_risk_exposure
    assert len(peel_risk.contributing_factors) >= 5
    assert len(peel_risk.supporting_finding_ids) >= 1
    assert peel_risk.scoring_rule_version == "1.0"
    assert len(normal_risk.counter_evidence) >= 1


def test_mixer_exposure_is_capped_and_not_equated_with_criminality(engine: ForensicEngine) -> None:
    mixer_bundle = engine.analyze_case(make_mixer_pattern_case())
    risk = mixer_bundle.risk_response
    assert risk.known_risk_exposure <= engine.config.risk_scoring.mixer_exposure_cap_without_illicit_link
    assert any("mixer" in lim.lower() for lim in risk.confidence_limitations)


def test_incomplete_graph_degrades_coverage_and_attribution_confidence(engine: ForensicEngine) -> None:
    incomplete_bundle = engine.analyze_case(make_incomplete_graph_case())
    complete_bundle = engine.analyze_case(make_peel_chain_eth_case())

    assert incomplete_bundle.risk_response.investigation_coverage < 0.7
    assert (
        incomplete_bundle.risk_response.investigation_coverage
        < complete_bundle.risk_response.investigation_coverage
    )
    assert (
        incomplete_bundle.risk_response.attribution_confidence
        < complete_bundle.risk_response.attribution_confidence
    )
    assert any("incomplete" in note.lower() for note in incomplete_bundle.risk_response.confidence_limitations)


def test_probable_end_receiver_ranking_orders_sink_first_without_identity_claims(
    engine: ForensicEngine,
) -> None:
    peel_bundle = engine.analyze_case(make_peel_chain_eth_case())
    receivers = peel_bundle.risk_response.probable_end_receivers
    assert len(receivers) >= 2
    assert receivers[0].rank == 1
    assert receivers[0].candidate_destination == "0xFinalSink"
    assert receivers[0].ranking_score >= receivers[1].ranking_score
    assert any("does not identify" in lim.lower() for lim in receivers[0].limitations)

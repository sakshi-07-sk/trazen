"""Deterministic test datasets covering all 11 forensic & false-positive scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Set

from forensics.schemas.input import (
    EntityLabel,
    GraphEdge,
    GraphNode,
    InvestigationCase,
    NormalizedTransaction,
    UTXOEntry,
)


BASE_TIME = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ScenarioExpectation:
    case: InvestigationCase
    expected_rule_ids: Set[str]
    forbidden_rule_ids: Set[str]
    description: str


def _eth_tx(
    tx_id: str,
    sender: str,
    receiver: str,
    value: float,
    minutes_offset: int,
    *,
    is_contract_call: bool = False,
    is_bridge: bool = False,
    status: str = "confirmed",
) -> NormalizedTransaction:
    return NormalizedTransaction(
        tx_id=tx_id,
        chain="ethereum",
        timestamp=BASE_TIME + timedelta(minutes=minutes_offset),
        from_address=sender,
        to_address=receiver,
        value=value,
        fee=0.002,
        asset="ETH",
        is_contract_call=is_contract_call,
        is_bridge_interaction=is_bridge,
        relationship_status=status,  # type: ignore[arg-type]
    )


def make_normal_wallet_case() -> InvestigationCase:
    """1. Normal retail wallet activity (negative test case)."""
    txs = [
        _eth_tx("TX-NORM-1", "0xEmployer", "0xAlice", 2.0, 0),
        _eth_tx("TX-NORM-2", "0xAlice", "0xCoffeeShop", 0.08, 120),
        _eth_tx("TX-NORM-3", "0xAlice", "0xDexPool", 0.45, 1500, is_contract_call=True),
        _eth_tx("TX-NORM-4", "0xDexPool", "0xAlice", 0.42, 1505, is_contract_call=True),
        _eth_tx("TX-NORM-5", "0xAlice", "0xFriendBob", 0.25, 4200),
    ]
    labels = [
        EntityLabel(address="0xDexPool", label="Uniswap V3 Pool", category="defi_router", verified=True, provenance="registry"),
        EntityLabel(address="0xCoffeeShop", label="Coffee Merchant", category="merchant", verified=True, provenance="registry"),
    ]
    return InvestigationCase(
        investigation_id="CASE-NORMAL-01",
        title="Normal retail wallet behaviour",
        chain="ethereum",
        seed_addresses=["0xAlice"],
        transactions=txs,
        labels=labels,
    )


def make_peel_chain_eth_case() -> InvestigationCase:
    """2a. Multi-hop Ethereum peel chain (5 hops, ~90% continuation each hop)."""
    txs = [
        _eth_tx("TX-PEEL-1", "0xSeed", "0xHop1", 100.0, 0),
        _eth_tx("TX-PEEL-2", "0xHop1", "0xHop2", 90.0, 15),
        _eth_tx("TX-PEEL-3", "0xHop1", "0xOfframpA", 9.5, 18),
        _eth_tx("TX-PEEL-4", "0xHop2", "0xHop3", 81.0, 35),
        _eth_tx("TX-PEEL-5", "0xHop2", "0xOfframpB", 8.5, 40),
        _eth_tx("TX-PEEL-6", "0xHop3", "0xHop4", 73.0, 60),
        _eth_tx("TX-PEEL-7", "0xHop4", "0xFinalSink", 65.5, 90),
    ]
    return InvestigationCase(
        investigation_id="CASE-PEEL-ETH-01",
        title="Ethereum 5-hop peel chain",
        chain="ethereum",
        seed_addresses=["0xSeed"],
        transactions=txs,
        labels=[
            EntityLabel(
                address="0xSeed",
                label="Reported Exploit Drainer",
                category="exploit",
                risk_indicator="critical",
                verified=True,
                provenance="incident_feed",
            )
        ],
    )


def make_peel_chain_btc_case() -> InvestigationCase:
    """2b. Multi-hop Bitcoin UTXO peel chain with change + peeled outputs."""
    txs = [
        NormalizedTransaction(
            tx_id="BTC-PEEL-1",
            chain="bitcoin",
            timestamp=BASE_TIME,
            asset="BTC",
            inputs=[UTXOEntry(address="bc1qSeed", value=10.0)],
            outputs=[
                UTXOEntry(address="bc1qHop1", value=9.0, output_index=0),
                UTXOEntry(address="bc1qPeel1", value=0.99, output_index=1),
            ],
        ),
        NormalizedTransaction(
            tx_id="BTC-PEEL-2",
            chain="bitcoin",
            timestamp=BASE_TIME + timedelta(minutes=25),
            asset="BTC",
            inputs=[UTXOEntry(address="bc1qHop1", value=9.0)],
            outputs=[
                UTXOEntry(address="bc1qHop2", value=8.1, output_index=0),
                UTXOEntry(address="bc1qPeel2", value=0.89, output_index=1),
            ],
        ),
        NormalizedTransaction(
            tx_id="BTC-PEEL-3",
            chain="bitcoin",
            timestamp=BASE_TIME + timedelta(minutes=55),
            asset="BTC",
            inputs=[UTXOEntry(address="bc1qHop2", value=8.1)],
            outputs=[
                UTXOEntry(address="bc1qHop3", value=7.3, output_index=0),
                UTXOEntry(address="bc1qPeel3", value=0.79, output_index=1),
            ],
        ),
        NormalizedTransaction(
            tx_id="BTC-PEEL-4",
            chain="bitcoin",
            timestamp=BASE_TIME + timedelta(minutes=80),
            asset="BTC",
            inputs=[UTXOEntry(address="bc1qHop3", value=7.3)],
            outputs=[
                UTXOEntry(address="bc1qFinalSink", value=6.6, output_index=0),
                UTXOEntry(address="bc1qPeel4", value=0.69, output_index=1),
            ],
        ),
    ]
    return InvestigationCase(
        investigation_id="CASE-PEEL-BTC-01",
        title="Bitcoin UTXO peel chain",
        chain="bitcoin",
        seed_addresses=["bc1qSeed"],
        transactions=txs,
    )


def make_fan_in_case() -> InvestigationCase:
    """3. High fan-in aggregation collector."""
    txs = [
        _eth_tx(f"TX-FIN-{i}", f"0xSender{i}", "0xCollector", 1.2 + 0.1 * i, i * 10)
        for i in range(1, 8)
    ]
    txs.append(_eth_tx("TX-FIN-OUT", "0xCollector", "0xVault", 9.8, 120))
    return InvestigationCase(
        investigation_id="CASE-FANIN-01",
        title="High fan-in aggregation",
        chain="ethereum",
        seed_addresses=["0xSender1"],
        transactions=txs,
    )


def make_fan_out_case() -> InvestigationCase:
    """4. High fan-out distribution."""
    txs = [_eth_tx("TX-FOUT-IN", "0xTreasury", "0xDistributor", 20.0, 0)]
    txs.extend(
        _eth_tx(f"TX-FOUT-{i}", "0xDistributor", f"0xRecip{i}", 2.4 + 0.1 * i, 10 + i * 5)
        for i in range(1, 8)
    )
    return InvestigationCase(
        investigation_id="CASE-FANOUT-01",
        title="High fan-out distribution",
        chain="ethereum",
        seed_addresses=["0xTreasury"],
        transactions=txs,
    )


def make_mixer_pattern_case() -> InvestigationCase:
    """5. Mixer-like equal-denomination pooling with rapid turnaround."""
    txs: List[NormalizedTransaction] = []
    for i in range(1, 6):
        txs.append(_eth_tx(f"TX-MIX-IN-{i}", f"0xDep{i}", "0xMixPool", 1.0, i * 10))
        txs.append(_eth_tx(f"TX-MIX-OUT-{i}", "0xMixPool", f"0xWith{i}", 0.995, i * 10 + 15))
    return InvestigationCase(
        investigation_id="CASE-MIXER-01",
        title="Mixer equal-denomination pattern",
        chain="ethereum",
        seed_addresses=["0xDep1"],
        transactions=txs,
        labels=[
            EntityLabel(
                address="0xMixPool",
                label="Fixed-Denom Privacy Pool",
                category="mixer",
                risk_indicator="medium",
                verified=True,
                provenance="community_registry",
            )
        ],
    )


def make_structuring_case() -> InvestigationCase:
    """6. Structuring: rapid repeated splits just below threshold + rapid pass-through."""
    txs = [
        _eth_tx("TX-STR-IN", "0xFundingSource", "0xSmurfHub", 22.0, 0),
        _eth_tx("TX-STR-1", "0xSmurfHub", "0xSub1", 4.7, 5),
        _eth_tx("TX-STR-2", "0xSmurfHub", "0xSub2", 4.6, 10),
        _eth_tx("TX-STR-3", "0xSmurfHub", "0xSub3", 4.8, 15),
        _eth_tx("TX-STR-4", "0xSmurfHub", "0xSub4", 4.5, 20),
        _eth_tx("TX-STR-5", "0xSmurfHub", "0xSub5", 3.3, 25),
    ]
    return InvestigationCase(
        investigation_id="CASE-STRUCT-01",
        title="Threshold-avoidance structuring & rapid pass-through",
        chain="ethereum",
        seed_addresses=["0xFundingSource"],
        transactions=txs,
    )


def make_dormant_activation_case() -> InvestigationCase:
    """7. Dormant wallet reactivating after 90 days with an outbound burst."""
    txs = [
        _eth_tx("TX-DORM-0", "0xGenesis", "0xSleeper", 15.0, 0),
        _eth_tx("TX-DORM-1", "0xSleeper", "0xDestA", 5.0, 90 * 24 * 60),
        _eth_tx("TX-DORM-2", "0xSleeper", "0xDestB", 5.0, 90 * 24 * 60 + 20),
        _eth_tx("TX-DORM-3", "0xSleeper", "0xDestC", 4.9, 90 * 24 * 60 + 40),
    ]
    return InvestigationCase(
        investigation_id="CASE-DORMANT-01",
        title="Dormant wallet reactivation",
        chain="ethereum",
        seed_addresses=["0xSleeper"],
        transactions=txs,
    )


def make_false_positive_exchange_hot_wallet_case() -> InvestigationCase:
    """8a. Negative test: High-volume exchange hot wallet with varied amounts (NOT a mixer/structuring)."""
    txs: List[NormalizedTransaction] = []
    for i in range(1, 10):
        txs.append(_eth_tx(f"TX-EX-IN-{i}", f"0xUserIn{i}", "0xExchangeHot", 0.37 * i, i * 12))
        txs.append(_eth_tx(f"TX-EX-OUT-{i}", "0xExchangeHot", f"0xUserOut{i}", 1.13 * i, i * 12 + 8))
    return InvestigationCase(
        investigation_id="CASE-FP-EXCHANGE-01",
        title="False positive guard: Exchange hot wallet",
        chain="ethereum",
        seed_addresses=["0xUserIn1"],
        transactions=txs,
        labels=[
            EntityLabel(
                address="0xExchangeHot",
                label="Major CEX Hot Wallet",
                category="exchange",
                risk_indicator="none",
                verified=True,
                provenance="exchange_disclosure",
            )
        ],
    )


def make_false_positive_payroll_case() -> InvestigationCase:
    """8b. Negative test: Payroll wallet sending equal salaries monthly (NOT structuring/fan-out alert)."""
    txs = [_eth_tx("TX-PAY-FUND", "0xCorpTreasury", "0xPayroll", 25.0, 0)]
    for i in range(1, 7):
        txs.append(_eth_tx(f"TX-PAY-{i}", "0xPayroll", f"0xEmployee{i}", 3.5, 5 + i))
    return InvestigationCase(
        investigation_id="CASE-FP-PAYROLL-01",
        title="False positive guard: Corporate payroll batch",
        chain="ethereum",
        seed_addresses=["0xCorpTreasury"],
        transactions=txs,
        labels=[
            EntityLabel(
                address="0xPayroll",
                label="Acme Corp Payroll",
                category="payroll",
                risk_indicator="none",
                verified=True,
                provenance="corporate_kyb",
            )
        ],
    )


def make_collaborative_coinjoin_case() -> InvestigationCase:
    """9. Negative test: Collaborative Bitcoin CoinJoin (must suppress CIOH clustering)."""
    txs = [
        NormalizedTransaction(
            tx_id="BTC-CJ-01",
            chain="bitcoin",
            timestamp=BASE_TIME,
            asset="BTC",
            inputs=[
                UTXOEntry(address="bc1qParticipantA", value=0.52),
                UTXOEntry(address="bc1qParticipantB", value=0.51),
                UTXOEntry(address="bc1qParticipantC", value=0.53),
                UTXOEntry(address="bc1qParticipantD", value=0.50),
            ],
            outputs=[
                UTXOEntry(address="bc1qMixOut1", value=0.50, output_index=0),
                UTXOEntry(address="bc1qMixOut2", value=0.50, output_index=1),
                UTXOEntry(address="bc1qMixOut3", value=0.50, output_index=2),
                UTXOEntry(address="bc1qMixOut4", value=0.50, output_index=3),
                UTXOEntry(address="bc1qChangeA", value=0.019, output_index=4),
                UTXOEntry(address="bc1qChangeB", value=0.009, output_index=5),
            ],
        )
    ]
    return InvestigationCase(
        investigation_id="CASE-BTC-COINJOIN-01",
        title="Collaborative CoinJoin transaction (CIOH safeguard)",
        chain="bitcoin",
        seed_addresses=["bc1qParticipantA"],
        transactions=txs,
    )


def make_incomplete_graph_case() -> InvestigationCase:
    """10. Missing / incomplete graph data (coverage must degrade & reflect limitations)."""
    nodes = [
        GraphNode(node_id="0xSeed", address="0xSeed", observed_in_full=True),
        GraphNode(
            node_id="0xMid",
            address="0xMid",
            observed_in_full=False,
            missing_neighbors_estimated=6,
        ),
        GraphNode(
            node_id="0xPartialSink",
            address="0xPartialSink",
            observed_in_full=False,
            missing_neighbors_estimated=3,
        ),
    ]
    edges = [
        GraphEdge(
            edge_id="E-1",
            source="0xSeed",
            target="0xMid",
            tx_ids=["TX-PART-1"],
            total_value=10.0,
            tx_count=1,
            relationship_status="confirmed",
        ),
        GraphEdge(
            edge_id="E-2",
            source="0xMid",
            target="0xPartialSink",
            tx_ids=[],
            total_value=8.0,
            tx_count=1,
            relationship_status="inferred",
            inference_reason="timing_correlation",
            confidence=0.60,
        ),
    ]
    return InvestigationCase(
        investigation_id="CASE-INCOMPLETE-01",
        title="Incomplete graph trace",
        chain="ethereum",
        seed_addresses=["0xSeed"],
        nodes=nodes,
        edges=edges,
        transactions=[_eth_tx("TX-PART-1", "0xSeed", "0xMid", 10.0, 0)],
        is_graph_complete=False,
        missing_data_notes=["Downstream RPC trace truncated at depth 2 due to rate limit."],
    )


def make_cross_case_shared_destination_cases() -> List[InvestigationCase]:
    """11. Multiple cases sharing an unlabelled downstream sink AND sharing a benign exchange."""
    shared_lbl = EntityLabel(
        address="0xSharedMajorCEX",
        label="Global Exchange Deposit",
        category="exchange",
        verified=True,
        provenance="registry",
    )
    case_a = InvestigationCase(
        investigation_id="CASE-CC-A",
        title="Cross-case Alpha",
        chain="ethereum",
        seed_addresses=["0xVictimA"],
        transactions=[
            _eth_tx("TX-CCA-1", "0xVictimA", "0xRelayX", 12.0, 0),
            _eth_tx("TX-CCA-2", "0xRelayX", "0xSharedInfraSink", 11.8, 20),
            _eth_tx("TX-CCA-3", "0xVictimA", "0xSharedMajorCEX", 1.0, 30),
        ],
        labels=[shared_lbl],
    )
    case_b = InvestigationCase(
        investigation_id="CASE-CC-B",
        title="Cross-case Beta",
        chain="ethereum",
        seed_addresses=["0xVictimB"],
        transactions=[
            _eth_tx("TX-CCB-1", "0xVictimB", "0xRelayX", 9.0, 100),
            _eth_tx("TX-CCB-2", "0xRelayX", "0xSharedInfraSink", 8.8, 120),
            _eth_tx("TX-CCB-3", "0xVictimB", "0xSharedMajorCEX", 2.0, 130),
        ],
        labels=[shared_lbl],
    )
    return [case_a, case_b]


def build_all_benchmark_scenarios() -> List[ScenarioExpectation]:
    """Return labelled scenario expectations for deterministic precision/recall tests."""
    return [
        ScenarioExpectation(
            case=make_normal_wallet_case(),
            expected_rule_ids=set(),
            forbidden_rule_ids={
                "PEEL-CHAIN-01",
                "MIXER-PATTERN-01",
                "STRUCTURING-SPLIT-01",
                "FAN-IN-01",
                "FAN-OUT-01",
                "DORMANT-REACTIVATION-01",
            },
            description="Normal retail activity",
        ),
        ScenarioExpectation(
            case=make_peel_chain_eth_case(),
            expected_rule_ids={"PEEL-CHAIN-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01"},
            description="Ethereum 5-hop peel chain",
        ),
        ScenarioExpectation(
            case=make_peel_chain_btc_case(),
            expected_rule_ids={"PEEL-CHAIN-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01"},
            description="Bitcoin UTXO 4-hop peel chain",
        ),
        ScenarioExpectation(
            case=make_fan_in_case(),
            expected_rule_ids={"FAN-IN-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01", "FAN-OUT-01"},
            description="Fan-in aggregation",
        ),
        ScenarioExpectation(
            case=make_fan_out_case(),
            expected_rule_ids={"FAN-OUT-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01", "FAN-IN-01"},
            description="Fan-out distribution",
        ),
        ScenarioExpectation(
            case=make_mixer_pattern_case(),
            expected_rule_ids={"MIXER-PATTERN-01"},
            forbidden_rule_ids={"PEEL-CHAIN-01"},
            description="Equal-denomination mixer pool",
        ),
        ScenarioExpectation(
            case=make_structuring_case(),
            expected_rule_ids={"STRUCTURING-SPLIT-01", "STRUCTURING-PASSTHROUGH-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01"},
            description="Threshold-avoidance structuring and rapid pass-through",
        ),
        ScenarioExpectation(
            case=make_dormant_activation_case(),
            expected_rule_ids={"DORMANT-REACTIVATION-01"},
            forbidden_rule_ids={"MIXER-PATTERN-01", "PEEL-CHAIN-01"},
            description="Dormant wallet reactivation",
        ),
        ScenarioExpectation(
            case=make_false_positive_exchange_hot_wallet_case(),
            expected_rule_ids=set(),
            forbidden_rule_ids={
                "MIXER-PATTERN-01",
                "FAN-IN-01",
                "FAN-OUT-01",
                "STRUCTURING-SPLIT-01",
                "PEEL-CHAIN-01",
            },
            description="High-volume exchange hot wallet negative test",
        ),
        ScenarioExpectation(
            case=make_false_positive_payroll_case(),
            expected_rule_ids=set(),
            forbidden_rule_ids={
                "MIXER-PATTERN-01",
                "FAN-OUT-01",
                "STRUCTURING-SPLIT-01",
            },
            description="Corporate payroll batch negative test",
        ),
        ScenarioExpectation(
            case=make_collaborative_coinjoin_case(),
            expected_rule_ids={"CLUSTER-COINJOIN-GUARD-01"},
            forbidden_rule_ids={"CLUSTER-HEURISTIC-01", "PEEL-CHAIN-01"},
            description="Collaborative CoinJoin CIOH suppression test",
        ),
    ]

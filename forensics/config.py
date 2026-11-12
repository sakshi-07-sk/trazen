"""Configuration loader for externalized forensic rules, thresholds, and weights."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "forensics_config.yaml"


class GeneralConfig(BaseModel):
    default_chain: str = "ethereum"
    dormancy_threshold_seconds: int = 2592000
    dormancy_reactivation_min_txs: int = 2


class ClusteringConfig(BaseModel):
    rule_version: str = "1.0"
    max_cioh_confidence: float = 0.72
    coinjoin_min_inputs: int = 3
    coinjoin_min_equal_outputs: int = 3
    coinjoin_value_tolerance: float = 0.005
    repeated_counterparty_min_txs: int = 4
    timing_window_seconds: int = 300
    min_timing_pair_count: int = 3
    cluster_confidence_cap: float = 0.85


class PeelChainConfig(BaseModel):
    rule_version: str = "1.0"
    min_hops: int = 3
    min_continuation_ratio: float = 0.65
    max_continuation_ratio: float = 0.995
    max_hop_delay_seconds: int = 86400
    min_hop_value_btc: float = 0.001
    min_hop_value_eth: float = 0.01


class MixerFanConfig(BaseModel):
    rule_version: str = "1.0"
    fan_in_min_unique_senders: int = 5
    fan_in_min_ratio: float = 0.70
    fan_out_min_unique_receivers: int = 5
    fan_out_min_ratio: float = 0.70
    mixer_min_inbound: int = 4
    mixer_min_outbound: int = 4
    mixer_equal_denomination_tolerance: float = 0.02
    mixer_min_equal_denomination_ratio: float = 0.55
    mixer_max_turnaround_seconds: int = 14400
    exchange_high_volume_min_txs: int = 20


class ChainStructuringThreshold(BaseModel):
    min_split_count: int = 4
    small_tx_upper_bound: float = 2.5
    reporting_reference_threshold: float = 5.0
    threshold_avoidance_lower_ratio: float = 0.70
    threshold_avoidance_upper_ratio: float = 0.99
    max_burst_window_seconds: int = 3600
    min_value_similarity_cv: float = 0.18
    rapid_passthrough_window_seconds: int = 1800
    rapid_passthrough_min_ratio: float = 0.80


class StructuringConfig(BaseModel):
    rule_version: str = "1.0"
    chains: Dict[str, ChainStructuringThreshold] = Field(default_factory=dict)

    def for_chain(self, chain: str) -> ChainStructuringThreshold:
        key = chain.lower()
        if key in self.chains:
            return self.chains[key]
        return self.chains.get("default", ChainStructuringThreshold())


class CrossCaseConfig(BaseModel):
    rule_version: str = "1.0"
    min_shared_cases: int = 2
    exclude_benign_public_hub_categories: List[str] = Field(
        default_factory=lambda: ["exchange", "cex", "payment_processor", "defi_router", "bridge"]
    )
    min_overlapping_path_length: int = 2


class RiskScoringConfig(BaseModel):
    rule_version: str = "1.0"
    priority_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "severity_score": 0.35,
            "finding_density": 0.20,
            "known_risk_exposure": 0.25,
            "anomaly_signal": 0.20,
        }
    )
    attribution_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "confirmed_edge_ratio": 0.40,
            "path_continuity": 0.25,
            "finding_confidence": 0.20,
            "investigation_coverage": 0.15,
        }
    )
    exposure_hop_decay: float = 0.55
    max_exposure_hops: int = 4
    mixer_exposure_cap_without_illicit_link: float = 0.45


class ReceiverRankingConfig(BaseModel):
    rule_version: str = "1.0"
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "trace_position": 0.20,
            "value_proportion": 0.25,
            "path_consistency": 0.20,
            "supporting_findings": 0.15,
            "label_provenance": 0.10,
            "investigation_coverage": 0.10,
        }
    )


class MLConfig(BaseModel):
    random_state: int = 42
    isolation_forest_contamination: float = 0.15
    dbscan_eps: float = 1.8
    dbscan_min_samples: int = 3


class ForensicsConfig(BaseModel):
    version: str = "1.0"
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    clustering: ClusteringConfig = Field(default_factory=ClusteringConfig)
    peel_chain: PeelChainConfig = Field(default_factory=PeelChainConfig)
    mixer_fan: MixerFanConfig = Field(default_factory=MixerFanConfig)
    structuring: StructuringConfig = Field(default_factory=StructuringConfig)
    cross_case: CrossCaseConfig = Field(default_factory=CrossCaseConfig)
    risk_scoring: RiskScoringConfig = Field(default_factory=RiskScoringConfig)
    receiver_ranking: ReceiverRankingConfig = Field(default_factory=ReceiverRankingConfig)
    ml: MLConfig = Field(default_factory=MLConfig)


@lru_cache(maxsize=4)
def load_config(config_path: str | None = None) -> ForensicsConfig:
    """Load and validate forensic engine configuration from YAML."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return ForensicsConfig()
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return ForensicsConfig.model_validate(raw)

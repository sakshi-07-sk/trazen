"""Configurable detection thresholds and canonical token registry for Role 3 security services."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class CanonicalTokenSpec:
    """Verified reference token identity keyed by (chain, contract_address)."""

    chain: str
    contract_address: str
    symbol: str
    name: str
    decimals: int


@dataclass(frozen=True)
class DustThresholdRule:
    """Asset-specific dusting threshold definition."""

    max_amount: Decimal
    min_repeat_count: int = 3
    burst_window_seconds: int = 3600
    spray_unique_targets: int = 5


DEFAULT_CANONICAL_TOKENS: tuple[CanonicalTokenSpec, ...] = (
    CanonicalTokenSpec(
        chain="ethereum",
        contract_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        symbol="USDC",
        name="USD Coin",
        decimals=6,
    ),
    CanonicalTokenSpec(
        chain="ethereum",
        contract_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
        symbol="USDT",
        name="Tether USD",
        decimals=6,
    ),
    CanonicalTokenSpec(
        chain="ethereum",
        contract_address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        symbol="WETH",
        name="Wrapped Ether",
        decimals=18,
    ),
    CanonicalTokenSpec(
        chain="ethereum",
        contract_address="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        symbol="WBTC",
        name="Wrapped BTC",
        decimals=8,
    ),
    CanonicalTokenSpec(
        chain="ethereum",
        contract_address="0x6b175474e89094c44da98b954eedeac495271d0f",
        symbol="DAI",
        name="Dai Stablecoin",
        decimals=18,
    ),
    CanonicalTokenSpec(
        chain="polygon",
        contract_address="0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
        symbol="USDC",
        name="USD Coin",
        decimals=6,
    ),
    CanonicalTokenSpec(
        chain="bsc",
        contract_address="0x55d398326f99059ff775485246999027b3197955",
        symbol="USDT",
        name="Tether USD",
        decimals=18,
    ),
    CanonicalTokenSpec(
        chain="solana",
        contract_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        symbol="USDC",
        name="USD Coin",
        decimals=6,
    ),
    CanonicalTokenSpec(
        chain="tron",
        contract_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        symbol="USDT",
        name="Tether USD",
        decimals=6,
    ),
)


def default_dust_rules() -> dict[str, DustThresholdRule]:
    """Return asset-aware default dusting thresholds (never a single universal threshold)."""
    return {
        "bitcoin:native:BTC": DustThresholdRule(max_amount=Decimal("0.00001")),
        "bitcoin:utxo:BTC": DustThresholdRule(max_amount=Decimal("0.00001")),
        "ethereum:native:ETH": DustThresholdRule(max_amount=Decimal("0.0001")),
        "polygon:native:POL": DustThresholdRule(max_amount=Decimal("0.01")),
        "bsc:native:BNB": DustThresholdRule(max_amount=Decimal("0.0005")),
        "solana:native:SOL": DustThresholdRule(max_amount=Decimal("0.001")),
        "tron:native:TRX": DustThresholdRule(max_amount=Decimal("0.1")),
        "ethereum:erc20:USDC": DustThresholdRule(max_amount=Decimal("0.05")),
        "ethereum:erc20:USDT": DustThresholdRule(max_amount=Decimal("0.05")),
        "ethereum:erc20:DAI": DustThresholdRule(max_amount=Decimal("0.05")),
        "ethereum:erc20:WBTC": DustThresholdRule(max_amount=Decimal("0.00001")),
        "polygon:erc20:USDC": DustThresholdRule(max_amount=Decimal("0.05")),
        "bsc:erc20:USDT": DustThresholdRule(max_amount=Decimal("0.05")),
        "solana:spl:USDC": DustThresholdRule(max_amount=Decimal("0.05")),
        "tron:trc20:USDT": DustThresholdRule(max_amount=Decimal("0.05")),
    }


@dataclass
class DetectionThresholds:
    """Injectable threshold bundle for all Role 3 security detectors."""

    # Address similarity & poisoning thresholds
    min_prefix_match_chars: int = 4
    min_suffix_match_chars: int = 4
    min_levenshtein_similarity: float = 0.55
    min_combined_similarity: float = 0.60
    poisoning_decoy_max_amount: Decimal = Decimal("0.01")
    poisoning_repeat_appearance_threshold: int = 2

    # Dusting thresholds keyed by "{chain}:{transfer_type}:{symbol}" or contract override
    dust_rules: dict[str, DustThresholdRule] = field(default_factory=default_dust_rules)
    contract_dust_overrides: dict[tuple[str, str], DustThresholdRule] = field(default_factory=dict)
    default_token_dust_decimals_scale: int = 2
    dust_ordinary_ratio_to_median: Decimal = Decimal("0.05")

    # Token impersonation thresholds
    token_name_similarity_threshold: float = 0.80
    token_contract_prefix_match_chars: int = 4
    token_contract_suffix_match_chars: int = 4
    canonical_tokens: tuple[CanonicalTokenSpec, ...] = DEFAULT_CANONICAL_TOKENS

    # Blockchain validation limits
    max_future_timestamp_skew_seconds: int = 600
    min_valid_block_year: int = 2009

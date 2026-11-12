"""Unit & negative tests for asset-aware dusting attack detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from cryptotrace.schemas.security_common import FindingCategory
from cryptotrace.schemas.security_inputs import TransactionRecord, TransferType
from cryptotrace.services.security.dusting_detector import DustingDetector


@pytest.mark.unit
def test_asset_aware_thresholds_differ_across_btc_eth_and_tokens() -> None:
    detector = DustingDetector()

    btc_tx = TransactionRecord(
        chain="bitcoin",
        asset_symbol="BTC",
        decimals=8,
        transfer_type=TransferType.NATIVE,
    )
    eth_tx = TransactionRecord(
        chain="ethereum",
        asset_symbol="ETH",
        decimals=18,
        transfer_type=TransferType.NATIVE,
    )
    usdc_tx = TransactionRecord(
        chain="ethereum",
        asset_symbol="USDC",
        token_contract="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        decimals=6,
        transfer_type=TransferType.ERC20,
    )

    btc_rule, _ = detector.resolve_threshold(btc_tx)
    eth_rule, _ = detector.resolve_threshold(eth_tx)
    usdc_rule, _ = detector.resolve_threshold(usdc_tx)

    assert btc_rule.max_amount < eth_rule.max_amount < usdc_rule.max_amount


@pytest.mark.unit
def test_dusting_spray_pattern_is_detected() -> None:
    detector = DustingDetector()
    t0 = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    attacker = "0xdddddddddddddddddddddddddddddddddddddddd"

    txs = [
        TransactionRecord(
            tx_hash=f"0x{idx:064x}",
            chain="ethereum",
            block_number=21_000_000 + idx,
            timestamp=t0 + timedelta(seconds=idx * 20),
            from_address=attacker,
            to_address=f"0x{idx + 100:040x}",
            amount=Decimal("0.00001"),
            asset_symbol="ETH",
            transfer_type=TransferType.NATIVE,
        )
        for idx in range(1, 7)
    ]

    findings = detector.analyze(investigation_id="inv-dust-1", transactions=txs)
    assert len(findings) == 1
    assert findings[0].finding_category == FindingCategory.DUSTING_ATTACK
    assert len(findings[0].supporting_transaction_refs) == 6


@pytest.mark.unit
def test_ordinary_small_payments_exchanges_and_airdrops_not_flagged_as_dusting() -> None:
    """Negative test: single small payment, exchange payout, and airdrop claim must not trigger."""
    detector = DustingDetector()
    t0 = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    wallet = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    exchange = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

    txs = [
        TransactionRecord(
            tx_hash="0x" + "1" * 64,
            chain="ethereum",
            timestamp=t0,
            from_address="0x1111111111111111111111111111111111111111",
            to_address=wallet,
            amount=Decimal("0.00005"),
            asset_symbol="ETH",
            transfer_type=TransferType.NATIVE,
        ),
        *[
            TransactionRecord(
                tx_hash=f"0x{i + 10:064x}",
                chain="ethereum",
                timestamp=t0 + timedelta(minutes=i),
                from_address=exchange,
                to_address=wallet,
                amount=Decimal("0.00002"),
                asset_symbol="ETH",
                transfer_type=TransferType.NATIVE,
                is_exchange_transfer=True,
            )
            for i in range(4)
        ],
        *[
            TransactionRecord(
                tx_hash=f"0x{i + 30:064x}",
                chain="ethereum",
                timestamp=t0 + timedelta(minutes=i),
                from_address="0x2222222222222222222222222222222222222222",
                to_address=f"0x{i + 200:040x}",
                amount=Decimal("0.01"),
                asset_symbol="USDC",
                token_contract="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                decimals=6,
                transfer_type=TransferType.ERC20,
                is_airdrop_claim=True,
            )
            for i in range(6)
        ],
    ]

    findings = detector.analyze(
        investigation_id="inv-dust-benign",
        transactions=txs,
        known_exchange_addresses={exchange},
    )
    assert findings == []


@pytest.mark.unit
def test_repeated_target_dust_deposits_from_distinct_senders_flagged() -> None:
    detector = DustingDetector()
    t0 = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    victim = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    txs = [
        TransactionRecord(
            tx_hash=f"0x{i:064x}",
            chain="ethereum",
            timestamp=t0 + timedelta(hours=i),
            from_address=f"0x{i + 10:040x}",
            to_address=victim,
            amount=Decimal("2.0"),
            asset_symbol="ETH",
            transfer_type=TransferType.NATIVE,
        )
        for i in range(1, 5)
    ] + [
        TransactionRecord(
            tx_hash=f"0x{i + 50:064x}",
            chain="ethereum",
            timestamp=t0 + timedelta(days=1, minutes=i),
            from_address=f"0x{i + 500:040x}",
            to_address=victim,
            amount=Decimal("0.00001"),
            asset_symbol="ETH",
            transfer_type=TransferType.NATIVE,
        )
        for i in range(1, 5)
    ]

    findings = detector.analyze(investigation_id="inv-dust-target", transactions=txs)
    assert len(findings) == 1
    assert findings[0].finding_type == "repeated_target_dust_deposits"


"""Tests for Transaction Normalization Pipeline and Precision."""

from decimal import Decimal
import pytest
from cryptotrace.core.exceptions import DataNormalizationError
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer
from cryptotrace.normalization.ethereum_normalizer import EthereumNormalizer
from cryptotrace.normalization.pipeline import NormalizationPipeline
from cryptotrace.schemas.common import BlockchainType


def test_missing_tx_hash_raises_error():
    with pytest.raises(DataNormalizationError) as exc_info:
        BitcoinNormalizer.normalize({})
    assert "missing txid/hash" in str(exc_info.value)

    with pytest.raises(DataNormalizationError) as exc_info:
        EthereumNormalizer.normalize({})
    assert "missing tx hash" in str(exc_info.value)


def test_decimal_precision_strictness():
    """Verify monetary amounts are strictly Decimal and do not suffer from float inaccuracies."""
    raw_btc = {
        "txid": "b" * 64,
        "status": {"confirmed": True, "block_height": 100, "block_hash": "c" * 64},
        "vin": [{"txid": "a" * 64, "vout": 0, "prevout": {"value": 100000000, "scriptpubkey_address": "addr1"}}],
        "vout": [
            {"value": 70000000, "scriptpubkey_address": "addr2"},
            {"value": 29990000, "scriptpubkey_address": "addr3"},
        ],
        "fee": 10000,
    }

    canonical = NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.BITCOIN,
        raw_payload=raw_btc,
    )

    assert isinstance(canonical.amount, Decimal)
    assert isinstance(canonical.fee, Decimal)
    # 70000000 + 29990000 = 99990000 sats = 0.99990000 BTC
    assert canonical.amount == Decimal("0.99990000")
    # Fee: 10000 sats = 0.00010000 BTC
    assert canonical.fee == Decimal("0.00010000")
    # Exact sum: 0.99990000 + 0.00010000 == 1.00000000
    assert canonical.amount + canonical.fee == Decimal("1.00000000")


def test_data_provenance_cryptographic_hash():
    raw_eth = {
        "hash": "0x" + "1" * 64,
        "blockNumber": 100,
        "from": "0x" + "2" * 40,
        "to": "0x" + "3" * 40,
        "value": "1000000000000000000",
    }
    canonical = NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.ETHEREUM,
        raw_payload=raw_eth,
    )

    assert canonical.provenance.raw_payload_hash is not None
    assert len(canonical.provenance.raw_payload_hash) == 64  # SHA-256 length

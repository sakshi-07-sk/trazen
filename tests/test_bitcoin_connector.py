"""Tests for Bitcoin Connector and UTXO Architecture."""

from decimal import Decimal
import pytest
from cryptotrace.connectors.fixtures.btc_samples import (
    BTC_SAMPLE_ADDRESS_1,
    BTC_SAMPLE_ADDRESS_2,
    BTC_SAMPLE_ADDRESS_3,
    BTC_SAMPLE_TX_1,
)
from cryptotrace.connectors.fixtures.mock_provider import BitcoinMockAdapter
from cryptotrace.core.exceptions import InvalidAddressError, InvalidHashError, ProviderError
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer


@pytest.mark.asyncio
async def test_bitcoin_address_validation(btc_mock_adapter: BitcoinMockAdapter):
    assert btc_mock_adapter.validate_address(BTC_SAMPLE_ADDRESS_1) is True
    assert btc_mock_adapter.validate_address(BTC_SAMPLE_ADDRESS_2) is True
    assert btc_mock_adapter.validate_address(BTC_SAMPLE_ADDRESS_3) is True

    # Invalid addresses
    assert btc_mock_adapter.validate_address("") is False
    assert btc_mock_adapter.validate_address("invalid_address_format") is False
    assert btc_mock_adapter.validate_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e") is False


@pytest.mark.asyncio
async def test_bitcoin_invalid_address_exception(btc_mock_adapter: BitcoinMockAdapter):
    with pytest.raises(InvalidAddressError) as exc_info:
        await btc_mock_adapter.get_address_info("bad_btc_address")
    assert exc_info.value.status_code == 400
    assert "Invalid bitcoin address format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_bitcoin_tx_hash_validation(btc_mock_adapter: BitcoinMockAdapter):
    valid_hash = BTC_SAMPLE_TX_1["txid"]
    assert btc_mock_adapter.validate_tx_hash(valid_hash) is True

    # Invalid hashes
    assert btc_mock_adapter.validate_tx_hash("short_hash") is False
    assert btc_mock_adapter.validate_tx_hash("0x" + valid_hash) is False  # 66 chars
    assert btc_mock_adapter.validate_tx_hash("Z" * 64) is False  # non-hex


@pytest.mark.asyncio
async def test_bitcoin_invalid_tx_hash_exception(btc_mock_adapter: BitcoinMockAdapter):
    with pytest.raises(InvalidHashError) as exc_info:
        await btc_mock_adapter.get_transaction("1234notahash")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_bitcoin_get_address_info(btc_mock_adapter: BitcoinMockAdapter):
    info = await btc_mock_adapter.get_address_info(BTC_SAMPLE_ADDRESS_1)
    assert info["address"] == BTC_SAMPLE_ADDRESS_1
    assert info["chain_stats"]["tx_count"] == 6
    assert info["_is_fixture"] is True
    assert "_raw_hash" in info


@pytest.mark.asyncio
async def test_bitcoin_get_transaction(btc_mock_adapter: BitcoinMockAdapter):
    tx = await btc_mock_adapter.get_transaction(BTC_SAMPLE_TX_1["txid"])
    assert tx["txid"] == BTC_SAMPLE_TX_1["txid"]
    assert len(tx["vin"]) == 2
    assert len(tx["vout"]) == 2
    assert tx["status"]["confirmed"] is True


@pytest.mark.asyncio
async def test_bitcoin_unknown_tx_raises_provider_error(btc_mock_adapter: BitcoinMockAdapter):
    random_hash = "a" * 64
    with pytest.raises(ProviderError) as exc_info:
        await btc_mock_adapter.get_transaction(random_hash)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_bitcoin_multi_input_multi_output_normalization():
    canonical = BitcoinNormalizer.normalize(BTC_SAMPLE_TX_1, provider_name="fixture_provider")

    assert canonical.blockchain.value == "bitcoin"
    assert canonical.tx_hash == BTC_SAMPLE_TX_1["txid"]
    assert len(canonical.inputs) == 2
    assert len(canonical.outputs) == 2

    # Inputs: 1.5 BTC + 2.5 BTC = 4.0 BTC
    total_in = sum(inp.amount_btc for inp in canonical.inputs)
    assert total_in == Decimal("4.0")

    # Outputs: 3.2 BTC + 0.799858 BTC = 3.999858 BTC
    total_out = sum(out.amount_btc for out in canonical.outputs)
    assert total_out == Decimal("3.999858")

    # Fee: 14200 sats = 0.000142 BTC
    assert canonical.fee == Decimal("0.000142")
    assert total_in == total_out + canonical.fee

    # Correct sender and recipient address lists
    assert len(canonical.sender_references) == 2
    assert len(canonical.recipient_references) == 2
    assert canonical.provenance.is_fixture is True

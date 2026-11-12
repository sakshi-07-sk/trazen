"""Tests for Ethereum Connector and Account-Based Architecture."""

from decimal import Decimal
import pytest
from cryptotrace.connectors.fixtures.eth_samples import (
    ETH_SAMPLE_ADDRESS_1,
    ETH_SAMPLE_ADDRESS_2,
    ETH_SAMPLE_ADDRESS_3,
    ETH_SAMPLE_TX_1,
    ETH_SAMPLE_TX_2,
    ETH_USDT_CONTRACT,
)
from cryptotrace.connectors.fixtures.mock_provider import EthereumMockAdapter
from cryptotrace.core.exceptions import InvalidAddressError, InvalidHashError, ProviderError
from cryptotrace.normalization.ethereum_normalizer import EthereumNormalizer


@pytest.mark.asyncio
async def test_ethereum_address_validation(eth_mock_adapter: EthereumMockAdapter):
    assert eth_mock_adapter.validate_address(ETH_SAMPLE_ADDRESS_1) is True
    assert eth_mock_adapter.validate_address(ETH_SAMPLE_ADDRESS_2) is True
    assert eth_mock_adapter.validate_address(ETH_USDT_CONTRACT) is True

    # Invalid addresses
    assert eth_mock_adapter.validate_address("") is False
    assert eth_mock_adapter.validate_address("0x123") is False  # too short
    assert eth_mock_adapter.validate_address(ETH_SAMPLE_ADDRESS_1[2:]) is False  # missing 0x prefix
    assert eth_mock_adapter.validate_address("0x" + "Z" * 40) is False  # non-hex chars


@pytest.mark.asyncio
async def test_ethereum_invalid_address_exception(eth_mock_adapter: EthereumMockAdapter):
    with pytest.raises(InvalidAddressError) as exc_info:
        await eth_mock_adapter.get_address_info("0xInvalid")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_ethereum_tx_hash_validation(eth_mock_adapter: EthereumMockAdapter):
    assert eth_mock_adapter.validate_tx_hash(ETH_SAMPLE_TX_1["hash"]) is True

    # Invalid hashes
    assert eth_mock_adapter.validate_tx_hash("0x12345") is False
    assert eth_mock_adapter.validate_tx_hash(ETH_SAMPLE_TX_1["hash"][2:]) is False  # missing 0x


@pytest.mark.asyncio
async def test_ethereum_invalid_tx_hash_exception(eth_mock_adapter: EthereumMockAdapter):
    with pytest.raises(InvalidHashError) as exc_info:
        await eth_mock_adapter.get_transaction("0xNotAHash")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_ethereum_native_transfer_normalization():
    canonical = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")

    assert canonical.blockchain.value == "ethereum"
    assert canonical.tx_hash == ETH_SAMPLE_TX_1["hash"]
    assert canonical.from_address == ETH_SAMPLE_ADDRESS_1.lower()
    assert canonical.to_address == ETH_SAMPLE_ADDRESS_2.lower()

    # 2.5 ETH
    assert canonical.amount == Decimal("2.5")
    # Gas: 21000 * 32 Gwei (32000000000 Wei) = 672000000000000 Wei = 0.000672 ETH
    assert canonical.fee == Decimal("0.000672")
    assert canonical.gas_price_gwei == Decimal("32")
    assert canonical.gas_used == 21000
    assert canonical.asset_symbol == "ETH"
    assert len(canonical.token_transfers) == 0


@pytest.mark.asyncio
async def test_ethereum_erc20_transfer_normalization():
    canonical = EthereumNormalizer.normalize(ETH_SAMPLE_TX_2, provider_name="fixture_provider")

    assert canonical.blockchain.value == "ethereum"
    assert canonical.tx_hash == ETH_SAMPLE_TX_2["hash"]
    assert len(canonical.token_transfers) == 1

    transfer = canonical.token_transfers[0]
    assert transfer.token_symbol == "USDT"
    assert transfer.token_decimals == 6
    assert transfer.from_address == ETH_SAMPLE_ADDRESS_2.lower()
    assert transfer.to_address == ETH_SAMPLE_ADDRESS_3.lower()
    assert transfer.raw_value == "5000000000"
    assert transfer.amount == Decimal("5000.000000")

    # Primary asset symbol reflects token transfer when native ETH amount is 0
    assert canonical.asset_symbol == "USDT"
    assert canonical.provenance.is_fixture is True

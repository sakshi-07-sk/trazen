"""Deterministic Mock Blockchain Adapter for offline tests and fixture fallback."""

import hashlib
import json
import re
from typing import Any, Dict, List
from cryptotrace.connectors.base import BaseBlockchainAdapter
from cryptotrace.connectors.fixtures.btc_samples import (
    BTC_FIXTURE_DATABASE,
    BTC_TRANSACTIONS_BY_HASH,
)
from cryptotrace.connectors.fixtures.eth_samples import (
    ETH_FIXTURE_DATABASE,
    ETH_TRANSACTIONS_BY_HASH,
)
from cryptotrace.core.exceptions import InvalidAddressError, InvalidHashError, ProviderError
from cryptotrace.schemas.common import BlockchainType


class BitcoinMockAdapter(BaseBlockchainAdapter):
    """Bitcoin adapter serving deterministic offline fixtures."""

    def __init__(self) -> None:
        super().__init__(provider_name="fixture_provider", is_fixture=True)

    @property
    def blockchain(self) -> BlockchainType:
        return BlockchainType.BITCOIN

    def validate_address(self, address: str) -> bool:
        """Validate Bitcoin base58 or bech32 address format."""
        if not address or len(address) < 26 or len(address) > 90:
            return False
        # Matches P2PKH (1...), P2SH (3...), Bech32 segwit (bc1...)
        pattern = r"^(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{8,87})$"
        return bool(re.match(pattern, address))

    def validate_tx_hash(self, tx_hash: str) -> bool:
        """Validate 64-char hex transaction ID."""
        if not tx_hash or len(tx_hash) != 64:
            return False
        return bool(re.match(r"^[0-9a-fA-F]{64}$", tx_hash))

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "bitcoin")

        if address in BTC_FIXTURE_DATABASE:
            data = BTC_FIXTURE_DATABASE[address]
            return {
                "address": address,
                "chain_stats": data["chain_stats"],
                "mempool_stats": data["mempool_stats"],
                "_raw_hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
                "_is_fixture": True,
            }

        # Synthetic empty address
        empty_data = {
            "address": address,
            "chain_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
            "mempool_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
        }
        return {
            **empty_data,
            "_raw_hash": hashlib.sha256(json.dumps(empty_data, sort_keys=True).encode()).hexdigest(),
            "_is_fixture": True,
        }

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        if not self.validate_tx_hash(tx_hash):
            raise InvalidHashError(tx_hash, "bitcoin")

        if tx_hash in BTC_TRANSACTIONS_BY_HASH:
            tx = BTC_TRANSACTIONS_BY_HASH[tx_hash]
            return {
                **tx,
                "_raw_hash": hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest(),
                "_is_fixture": True,
            }

        raise ProviderError(
            provider=self.provider_name,
            message=f"Bitcoin transaction '{tx_hash}' not found in provider fixtures",
            code="TX_NOT_FOUND",
            status_code=404,
        )

    async def get_transactions_for_address(
        self, address: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "bitcoin")

        if address in BTC_FIXTURE_DATABASE:
            txs = BTC_FIXTURE_DATABASE[address].get("transactions", [])
            return [
                {
                    **tx,
                    "_raw_hash": hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest(),
                    "_is_fixture": True,
                }
                for tx in txs[offset : offset + limit]
            ]
        return []

    async def get_block(self, block_identifier: Any) -> Dict[str, Any]:
        block_height = int(block_identifier) if str(block_identifier).isdigit() else 830120
        payload = {
            "id": f"00000000000000000001a4e17ef1bc2cd56037f37f382a89cbff7d99cb29e248",
            "height": block_height,
            "version": 536870912,
            "timestamp": 1707800000,
            "tx_count": 2840,
            "size": 1650320,
            "weight": 3993200,
            "merkle_root": "a89d3810f3910c2830f810398012380129381092380129381029381029381029",
        }
        return {
            **payload,
            "_raw_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "_is_fixture": True,
        }


class EthereumMockAdapter(BaseBlockchainAdapter):
    """Ethereum adapter serving deterministic offline fixtures."""

    def __init__(self) -> None:
        super().__init__(provider_name="fixture_provider", is_fixture=True)

    @property
    def blockchain(self) -> BlockchainType:
        return BlockchainType.ETHEREUM

    def validate_address(self, address: str) -> bool:
        """Validate 20-byte 0x-prefixed hex Ethereum address."""
        if not address or len(address) != 42 or not address.startswith("0x"):
            return False
        return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))

    def validate_tx_hash(self, tx_hash: str) -> bool:
        """Validate 32-byte 0x-prefixed hex transaction hash."""
        if not tx_hash or len(tx_hash) != 66 or not tx_hash.startswith("0x"):
            return False
        return bool(re.match(r"^0x[0-9a-fA-F]{64}$", tx_hash))

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "ethereum")

        normalized = address.lower()
        if normalized in ETH_FIXTURE_DATABASE:
            entry = ETH_FIXTURE_DATABASE[normalized]
            return {
                "address": normalized,
                "balance_wei": entry["balance_wei"],
                "tx_count": entry["tx_count"],
                "is_contract": entry["is_contract"],
                "_raw_hash": hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest(),
                "_is_fixture": True,
            }

        empty_entry = {
            "address": normalized,
            "balance_wei": "0",
            "tx_count": 0,
            "is_contract": False,
        }
        return {
            **empty_entry,
            "_raw_hash": hashlib.sha256(json.dumps(empty_entry, sort_keys=True).encode()).hexdigest(),
            "_is_fixture": True,
        }

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        if not self.validate_tx_hash(tx_hash):
            raise InvalidHashError(tx_hash, "ethereum")

        lookup_hash = tx_hash.lower()
        if lookup_hash in ETH_TRANSACTIONS_BY_HASH:
            tx = ETH_TRANSACTIONS_BY_HASH[lookup_hash]
            return {
                **tx,
                "_raw_hash": hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest(),
                "_is_fixture": True,
            }

        raise ProviderError(
            provider=self.provider_name,
            message=f"Ethereum transaction '{tx_hash}' not found in provider fixtures",
            code="TX_NOT_FOUND",
            status_code=404,
        )

    async def get_transactions_for_address(
        self, address: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "ethereum")

        normalized = address.lower()
        if normalized in ETH_FIXTURE_DATABASE:
            txs = ETH_FIXTURE_DATABASE[normalized].get("transactions", [])
            return [
                {
                    **tx,
                    "_raw_hash": hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest(),
                    "_is_fixture": True,
                }
                for tx in txs[offset : offset + limit]
            ]
        return []

    async def get_block(self, block_identifier: Any) -> Dict[str, Any]:
        block_num = 19753072
        payload = {
            "number": hex(block_num),
            "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "parentHash": "0x9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef",
            "timestamp": "0x65ca35e0",
            "gasLimit": "0x1c9c380",
            "gasUsed": "0xc83b12",
            "transactions": [ETH_SAMPLE_TX_1["hash"]],
        }
        return {
            **payload,
            "_raw_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "_is_fixture": True,
        }

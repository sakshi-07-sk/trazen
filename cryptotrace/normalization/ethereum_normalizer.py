"""Ethereum Transaction Normalizer."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Any, Dict, List
from cryptotrace.core.exceptions import DataNormalizationError
from cryptotrace.schemas.common import BlockchainType, TransactionStatus
from cryptotrace.schemas.provenance import DataSourceProvenance
from cryptotrace.schemas.token import TokenTransfer
from cryptotrace.schemas.transaction import CanonicalTransaction


class EthereumNormalizer:
    """Normalizes raw Ethereum JSON-RPC / Etherscan transactions into CanonicalTransaction."""

    WEI_PER_ETH = Decimal("1000000000000000000")
    WEI_PER_GWEI = Decimal("1000000000")

    @staticmethod
    def _parse_int(val: Any, default: int = 0) -> int:
        if val is None:
            return default
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        if s.isdigit():
            return int(s)
        return default

    @classmethod
    def normalize(
        cls,
        raw_data: Dict[str, Any],
        chain_id: str = "1",
        provider_name: str = "etherscan",
    ) -> CanonicalTransaction:
        try:
            tx_hash = raw_data.get("hash")
            if not tx_hash:
                raise DataNormalizationError("Ethereum payload missing tx hash", raw_data)

            block_number = cls._parse_int(raw_data.get("blockNumber"))
            block_hash = raw_data.get("blockHash") or "0x0000000000000000000000000000000000000000000000000000000000000000"

            # Timestamp parsing
            timestamp_val = raw_data.get("timeStamp") or raw_data.get("timestamp")
            if timestamp_val:
                sec = cls._parse_int(timestamp_val)
                tx_timestamp = datetime.fromtimestamp(sec, tz=timezone.utc)
            else:
                tx_timestamp = datetime.now(timezone.utc)

            # Addresses
            from_addr = (raw_data.get("from") or "").lower()
            to_addr = (raw_data.get("to") or "").lower() or None

            # Monetary amounts (Wei -> ETH Decimal)
            raw_value = raw_data.get("value", "0")
            value_wei = cls._parse_int(raw_value)
            amount_eth = Decimal(str(value_wei)) / cls.WEI_PER_ETH

            # Gas and Fee
            gas_used = cls._parse_int(raw_data.get("gasUsed") or raw_data.get("gas", 21000))
            gas_price_wei = cls._parse_int(raw_data.get("gasPrice", 0))
            gas_price_gwei = Decimal(str(gas_price_wei)) / cls.WEI_PER_GWEI
            fee_eth = (Decimal(str(gas_used)) * Decimal(str(gas_price_wei))) / cls.WEI_PER_ETH

            # Nonce and Input
            nonce = cls._parse_int(raw_data.get("nonce"))
            input_data = raw_data.get("input") or "0x"
            is_contract = input_data != "0x" or bool(raw_data.get("contractAddress"))

            # Status and Confirmations
            # Etherscan: isError "0" == success, txreceipt_status "1" == success
            is_error = raw_data.get("isError") == "1" or raw_data.get("txreceipt_status") == "0"
            status = TransactionStatus.FAILED if is_error else TransactionStatus.CONFIRMED
            confirmations = cls._parse_int(raw_data.get("confirmations", 1))

            # Token Transfers (ERC-20)
            token_transfers: List[TokenTransfer] = []
            for item in raw_data.get("tokenTransfers", []):
                t_dec = int(item.get("token_decimals", 18))
                t_raw = str(item.get("raw_value", "0"))
                t_amt = Decimal(str(item.get("amount", "0")))
                if t_amt == Decimal("0") and t_raw != "0":
                    t_amt = Decimal(t_raw) / (Decimal(10) ** t_dec)

                tt = TokenTransfer(
                    token_address=item["token_address"].lower(),
                    token_symbol=item.get("token_symbol", "ERC20"),
                    token_name=item.get("token_name"),
                    token_decimals=t_dec,
                    from_address=item["from_address"].lower(),
                    to_address=item["to_address"].lower(),
                    raw_value=t_raw,
                    amount=t_amt,
                    log_index=item.get("log_index"),
                    transaction_hash=tx_hash,
                    block_number=block_number,
                )
                token_transfers.append(tt)

            # References
            sender_refs = [from_addr] if from_addr else []
            recipient_refs = [to_addr] if to_addr else []
            for tt in token_transfers:
                if tt.to_address not in recipient_refs:
                    recipient_refs.append(tt.to_address)

            # Primary asset
            asset_symbol = "ETH"
            if amount_eth == Decimal("0") and token_transfers:
                asset_symbol = token_transfers[0].token_symbol

            # Provenance
            raw_hash = raw_data.get("_raw_hash") or hashlib.sha256(
                json.dumps(raw_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            is_fixture = bool(raw_data.get("_is_fixture", False)) or provider_name == "fixture_provider"

            provenance = DataSourceProvenance(
                provider_name=provider_name,
                is_fixture=is_fixture,
                raw_payload_hash=raw_hash,
                provider_metadata={"nonce": nonce, "gas_used": gas_used},
            )

            return CanonicalTransaction(
                chain_id=chain_id,
                blockchain=BlockchainType.ETHEREUM,
                tx_hash=tx_hash,
                block_number=block_number,
                block_hash=block_hash,
                timestamp=tx_timestamp,
                sender_references=sender_refs,
                recipient_references=recipient_refs,
                asset_symbol=asset_symbol,
                contract_address=raw_data.get("contractAddress") or (to_addr if is_contract else None),
                amount=amount_eth,
                fee=fee_eth,
                status=status,
                confirmations=confirmations,
                provenance=provenance,
                from_address=from_addr,
                to_address=to_addr,
                gas_used=gas_used,
                gas_price_gwei=gas_price_gwei,
                nonce=nonce,
                input_data=input_data,
                is_contract_interaction=is_contract,
                token_transfers=token_transfers,
            )
        except Exception as e:
            if isinstance(e, DataNormalizationError):
                raise
            raise DataNormalizationError(f"Failed to normalize Ethereum transaction: {e}", raw_data)

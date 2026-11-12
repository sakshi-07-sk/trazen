"""Bitcoin Transaction Normalizer."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Any, Dict, List
from cryptotrace.core.exceptions import DataNormalizationError
from cryptotrace.schemas.common import BlockchainType, TransactionStatus
from cryptotrace.schemas.provenance import DataSourceProvenance
from cryptotrace.schemas.transaction import CanonicalTransaction
from cryptotrace.schemas.utxo import UTXOInput, UTXOOutput


class BitcoinNormalizer:
    """Normalizes raw Bitcoin transaction structures into CanonicalTransaction."""

    SATS_PER_BTC = Decimal("100000000")

    @classmethod
    def normalize(
        cls,
        raw_data: Dict[str, Any],
        chain_id: str = "btc-mainnet",
        provider_name: str = "blockstream",
    ) -> CanonicalTransaction:
        try:
            txid = raw_data.get("txid") or raw_data.get("hash")
            if not txid:
                raise DataNormalizationError("Bitcoin payload missing txid/hash", raw_data)

            # Block and status
            status_obj = raw_data.get("status", {})
            confirmed = status_obj.get("confirmed", True)
            block_height = status_obj.get("block_height", 0)
            block_hash = status_obj.get("block_hash", "0000000000000000000000000000000000000000000000000000000000000000")
            block_time = status_obj.get("block_time")

            if block_time:
                tx_timestamp = datetime.fromtimestamp(block_time, tz=timezone.utc)
            elif "time" in raw_data:
                tx_timestamp = datetime.fromtimestamp(raw_data["time"], tz=timezone.utc)
            else:
                tx_timestamp = datetime.now(timezone.utc)

            # Inputs (vin)
            inputs: List[UTXOInput] = []
            sender_references: List[str] = []
            for vin in raw_data.get("vin", []):
                prevout = vin.get("prevout") or {}
                amount_sats = int(prevout.get("value", 0))
                addr = prevout.get("scriptpubkey_address")
                if addr:
                    sender_references.append(addr)

                input_obj = UTXOInput(
                    prev_tx_hash=vin.get("txid", "coinbase"),
                    vout=int(vin.get("vout", 0)),
                    address=addr,
                    amount_sats=amount_sats,
                    amount_btc=Decimal(str(amount_sats)) / cls.SATS_PER_BTC,
                    sequence=vin.get("sequence"),
                    script_sig=vin.get("scriptsig"),
                    witness=vin.get("witness", []),
                )
                inputs.append(input_obj)

            # Outputs (vout)
            outputs: List[UTXOOutput] = []
            recipient_references: List[str] = []
            total_output_sats = 0
            for idx, vout in enumerate(raw_data.get("vout", [])):
                out_sats = int(vout.get("value", 0))
                total_output_sats += out_sats
                addr = vout.get("scriptpubkey_address")
                if addr:
                    recipient_references.append(addr)

                output_obj = UTXOOutput(
                    vout=idx,
                    address=addr,
                    amount_sats=out_sats,
                    amount_btc=Decimal(str(out_sats)) / cls.SATS_PER_BTC,
                    script_pubkey=vout.get("scriptpubkey"),
                    script_type=vout.get("scriptpubkey_type"),
                    is_spent=False,
                )
                outputs.append(output_obj)

            # Calculate Fee
            fee_sats = int(raw_data.get("fee", 0))
            if fee_sats == 0 and inputs and outputs:
                total_in = sum(i.amount_sats for i in inputs if i.prev_tx_hash != "coinbase")
                if total_in > total_output_sats:
                    fee_sats = total_in - total_output_sats
            fee_btc = Decimal(str(fee_sats)) / cls.SATS_PER_BTC

            total_amount_btc = Decimal(str(total_output_sats)) / cls.SATS_PER_BTC

            # Provenance
            raw_hash = raw_data.get("_raw_hash") or hashlib.sha256(
                json.dumps(raw_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            is_fixture = bool(raw_data.get("_is_fixture", False)) or provider_name == "fixture_provider"

            provenance = DataSourceProvenance(
                provider_name=provider_name,
                is_fixture=is_fixture,
                raw_payload_hash=raw_hash,
                provider_metadata={"size": raw_data.get("size"), "weight": raw_data.get("weight")},
            )

            return CanonicalTransaction(
                chain_id=chain_id,
                blockchain=BlockchainType.BITCOIN,
                tx_hash=txid,
                block_number=block_height,
                block_hash=block_hash,
                timestamp=tx_timestamp,
                sender_references=list(dict.fromkeys(sender_references)) or ["coinbase"],
                recipient_references=list(dict.fromkeys(recipient_references)) or ["unparsed_output"],
                asset_symbol="BTC",
                contract_address=None,
                amount=total_amount_btc,
                fee=fee_btc,
                status=TransactionStatus.CONFIRMED if confirmed else TransactionStatus.PENDING,
                confirmations=1 if confirmed else 0,
                provenance=provenance,
                inputs=inputs,
                outputs=outputs,
                vsize=raw_data.get("weight", 0) // 4 if raw_data.get("weight") else raw_data.get("size"),
                locktime=raw_data.get("locktime"),
            )
        except Exception as e:
            if isinstance(e, DataNormalizationError):
                raise
            raise DataNormalizationError(f"Failed to normalize Bitcoin transaction: {e}", raw_data)

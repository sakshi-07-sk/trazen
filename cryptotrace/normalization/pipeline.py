"""Universal Normalization Pipeline orchestrating chain-specific parsers."""

from typing import Any, Dict, Optional, Tuple
from cryptotrace.core.exceptions import DataNormalizationError
from cryptotrace.db.models.provenance import ProvenanceModel
from cryptotrace.db.models.token_transfer import TokenTransferModel
from cryptotrace.db.models.transaction import TransactionModel
from cryptotrace.db.models.utxo import UTXOModel
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer
from cryptotrace.normalization.ethereum_normalizer import EthereumNormalizer
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.transaction import CanonicalTransaction


class NormalizationPipeline:
    """Orchestrates normalization from raw provider JSON into CanonicalTransaction and ORM entities."""

    @classmethod
    def normalize_transaction(
        cls,
        blockchain: BlockchainType,
        raw_payload: Dict[str, Any],
        chain_id: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> CanonicalTransaction:
        """Route to appropriate chain parser and produce canonical schema."""
        if blockchain == BlockchainType.BITCOIN:
            return BitcoinNormalizer.normalize(
                raw_payload,
                chain_id=chain_id or "btc-mainnet",
                provider_name=provider_name or "blockstream",
            )
        elif blockchain == BlockchainType.ETHEREUM:
            return EthereumNormalizer.normalize(
                raw_payload,
                chain_id=chain_id or "1",
                provider_name=provider_name or "etherscan",
            )
        else:
            raise DataNormalizationError(f"Unsupported blockchain type: {blockchain}")

    @classmethod
    def to_orm(
        cls,
        canonical: CanonicalTransaction,
        investigation_id: Optional[str] = None,
    ) -> Tuple[TransactionModel, ProvenanceModel]:
        """Convert CanonicalTransaction into SQLAlchemy ORM entities with associated child records."""
        tx_model = TransactionModel(
            investigation_id=investigation_id,
            chain_id=canonical.chain_id,
            blockchain=canonical.blockchain.value,
            tx_hash=canonical.tx_hash,
            block_number=canonical.block_number,
            block_hash=canonical.block_hash,
            timestamp=canonical.timestamp,
            sender_references=canonical.sender_references,
            recipient_references=canonical.recipient_references,
            asset_symbol=canonical.asset_symbol,
            contract_address=canonical.contract_address,
            amount=canonical.amount,
            fee=canonical.fee,
            status=canonical.status.value,
            confirmations=canonical.confirmations,
            from_address=canonical.from_address,
            to_address=canonical.to_address,
            gas_used=canonical.gas_used,
            gas_price_gwei=canonical.gas_price_gwei,
            nonce=canonical.nonce,
            input_data=canonical.input_data,
            vsize=canonical.vsize,
            locktime=canonical.locktime,
            raw_payload_hash=canonical.provenance.raw_payload_hash,
            provider_name=canonical.provenance.provider_name,
            is_fixture=canonical.provenance.is_fixture,
            raw_payload=canonical.provenance.provider_metadata,
        )

        # Attach UTXOs for Bitcoin
        for vout in canonical.outputs:
            utxo = UTXOModel(
                tx_hash=canonical.tx_hash,
                vout=vout.vout,
                address=vout.address,
                amount_sats=vout.amount_sats,
                amount_btc=vout.amount_btc,
                script_pubkey=vout.script_pubkey,
                script_type=vout.script_type,
                is_spent=vout.is_spent,
                spending_tx_hash=vout.spending_tx_hash,
            )
            tx_model.utxos.append(utxo)

        # Attach Token Transfers for Ethereum
        for tt in canonical.token_transfers:
            token_m = TokenTransferModel(
                transaction_hash=canonical.tx_hash,
                token_address=tt.token_address,
                token_symbol=tt.token_symbol,
                token_name=tt.token_name,
                token_decimals=tt.token_decimals,
                from_address=tt.from_address,
                to_address=tt.to_address,
                raw_value=tt.raw_value,
                amount=tt.amount,
                log_index=tt.log_index,
                block_number=tt.block_number,
            )
            tx_model.token_transfers.append(token_m)

        # Provenance model
        prov_model = ProvenanceModel(
            record_type="transaction",
            record_identifier=canonical.tx_hash,
            provider_name=canonical.provenance.provider_name,
            provider_endpoint=canonical.provenance.provider_endpoint,
            retrieved_at=canonical.provenance.retrieved_at,
            is_fixture=canonical.provenance.is_fixture,
            raw_payload_hash=canonical.provenance.raw_payload_hash,
            response_latency_ms=canonical.provenance.response_latency_ms,
            provider_metadata=canonical.provenance.provider_metadata,
        )

        return tx_model, prov_model

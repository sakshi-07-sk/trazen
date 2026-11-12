"""Defensive blockchain data validation and multi-provider trust verification."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from pydantic import BaseModel, Field

from cryptotrace.schemas.findings import SecurityFinding, utc_now
from cryptotrace.schemas.security_common import (
    EVM_CHAINS,
    ChainId,
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    IndependentVerificationStatus,
    Severity,
    ValidationStatus,
)
from cryptotrace.schemas.security_inputs import ProviderObservation, TransactionRecord, TransferType
from cryptotrace.services.security.address_similarity import (
    normalize_chain_name,
    validate_and_normalize_address,
)
from cryptotrace.services.security.security_config import DetectionThresholds

_EVM_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_HEX64_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SOL_SIG_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,90}$")

_VALID_NETWORKS_BY_CHAIN: dict[str, set[str]] = {
    "ethereum": {"mainnet", "eth-mainnet", "sepolia", "eth-sepolia", "holesky", "1", "11155111"},
    "polygon": {"mainnet", "polygon-mainnet", "amoy", "137", "80002"},
    "bsc": {"mainnet", "bsc-mainnet", "testnet", "56", "97"},
    "arbitrum": {"mainnet", "arbitrum-one", "sepolia", "42161"},
    "optimism": {"mainnet", "op-mainnet", "sepolia", "10"},
    "base": {"mainnet", "base-mainnet", "sepolia", "8453"},
    "avalanche": {"mainnet", "c-chain", "fuji", "43114"},
    "bitcoin": {"mainnet", "btc-mainnet", "btc-testnet", "testnet", "signet", "regtest"},
    "solana": {"mainnet", "mainnet-beta", "devnet", "testnet"},
    "tron": {"mainnet", "tron-mainnet", "shasta", "nile"},
}


class IndependentProviderProtocol(Protocol):
    """Dependency-injected provider lookup interface (no direct RPC connectors here)."""

    provider_name: str
    upstream_source: str | None

    def fetch_transaction(self, chain: str, tx_hash: str) -> ProviderObservation | None:
        """Fetch an independent transaction observation for verification."""


class BlockchainValidationReport(BaseModel):
    """Structured outcome from defensive blockchain data validation."""

    validation_status: ValidationStatus
    independent_verification_status: IndependentVerificationStatus
    data_quality_warnings: list[str] = Field(default_factory=list)
    failed_reasons: list[str] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    source_provider: str | None = None
    verification_timestamp: datetime = Field(default_factory=utc_now)
    original_evidence_ref: str | None = None
    findings: list[SecurityFinding] = Field(default_factory=list)


def _to_decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        dec = Decimal(str(value))
        return dec if dec.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def validate_tx_hash_format(tx_hash: str, chain: str) -> tuple[bool, str | None]:
    """Validate transaction hash/signature syntax for the declared chain."""
    raw = tx_hash.strip()
    canon_chain = normalize_chain_name(chain)
    if not raw:
        return False, "Transaction hash is empty"
    if canon_chain in EVM_CHAINS:
        if not _EVM_HASH_RE.match(raw):
            return False, f"Invalid EVM tx_hash '{raw}' (expected 0x + 64 hex chars)"
        return True, None
    if canon_chain in (ChainId.BITCOIN.value, ChainId.TRON.value):
        if not _HEX64_HASH_RE.match(raw):
            return False, f"Invalid {canon_chain} tx_hash '{raw}' (expected 64 hex chars)"
        return True, None
    if canon_chain == ChainId.SOLANA.value:
        if not _SOL_SIG_RE.match(raw):
            return False, f"Invalid Solana tx signature '{raw}'"
        return True, None
    return False, f"Cannot validate tx_hash for unsupported chain '{chain}'"


def _is_bitcoin_synthetic_endpoint(addr: str | None, canon_chain: str) -> bool:
    if canon_chain != ChainId.BITCOIN.value or not addr:
        return False
    low = addr.strip().lower()
    return low == "coinbase" or low.startswith("coinbase:") or low.startswith("op_return:") or low == "unparsed_output"


class BlockchainDataValidator:
    """Defensive validator checking format, invariants, provenance, and multi-provider consistency."""

    def __init__(
        self,
        thresholds: DetectionThresholds | None = None,
        independent_providers: list[IndependentProviderProtocol] | None = None,
        require_independent_verification: bool = False,
    ) -> None:
        self.thresholds = thresholds or DetectionThresholds()
        self.independent_providers = independent_providers or []
        self.require_independent_verification = require_independent_verification

    def validate_transaction(
        self,
        investigation_id: str,
        tx: TransactionRecord,
        provider_observations: list[ProviderObservation] | None = None,
        require_independent: bool | None = None,
    ) -> BlockchainValidationReport:
        """Validate a single transaction record and optionally cross-check provider observations."""
        strict_indep = (
            self.require_independent_verification
            if require_independent is None
            else require_independent
        )

        failed_reasons: list[str] = []
        warnings: list[str] = []
        missing_mandatory: list[str] = []

        canon_chain = normalize_chain_name(tx.chain)
        if not canon_chain:
            missing_mandatory.append("chain")
        elif canon_chain not in _VALID_NETWORKS_BY_CHAIN:
            failed_reasons.append(f"Unsupported or unrecognized blockchain identifier '{tx.chain}'")

        if tx.network and canon_chain in _VALID_NETWORKS_BY_CHAIN:
            net_norm = tx.network.strip().lower()
            if net_norm not in _VALID_NETWORKS_BY_CHAIN[canon_chain]:
                failed_reasons.append(
                    f"Network '{tx.network}' is inconsistent with chain '{canon_chain}'"
                )

        if not tx.tx_hash:
            missing_mandatory.append("tx_hash")
        elif canon_chain in _VALID_NETWORKS_BY_CHAIN:
            ok_hash, hash_err = validate_tx_hash_format(tx.tx_hash, canon_chain)
            if not ok_hash and hash_err:
                failed_reasons.append(hash_err)

        is_utxo_tx_node_from = (
            canon_chain == ChainId.BITCOIN.value
            and tx.transfer_type == TransferType.UTXO
            and bool(tx.from_address and tx.from_address.lower().startswith("tx:"))
        )
        is_utxo_tx_node_to = (
            canon_chain == ChainId.BITCOIN.value
            and tx.transfer_type == TransferType.UTXO
            and bool(tx.to_address and tx.to_address.lower().startswith("tx:"))
        )

        if not tx.from_address:
            missing_mandatory.append("from_address")
        elif (
            canon_chain in _VALID_NETWORKS_BY_CHAIN
            and not is_utxo_tx_node_from
            and not _is_bitcoin_synthetic_endpoint(tx.from_address, canon_chain)
        ):
            from_val = validate_and_normalize_address(tx.from_address, canon_chain)
            if not from_val.is_valid:
                failed_reasons.append(f"Invalid from_address: {from_val.reason}")

        if not tx.to_address:
            missing_mandatory.append("to_address")
        elif (
            canon_chain in _VALID_NETWORKS_BY_CHAIN
            and not is_utxo_tx_node_to
            and not _is_bitcoin_synthetic_endpoint(tx.to_address, canon_chain)
        ):
            to_val = validate_and_normalize_address(tx.to_address, canon_chain)
            if not to_val.is_valid:
                failed_reasons.append(f"Invalid to_address: {to_val.reason}")

        if (
            tx.from_address
            and tx.to_address
            and canon_chain in _VALID_NETWORKS_BY_CHAIN
            and not is_utxo_tx_node_from
            and not is_utxo_tx_node_to
        ):
            f_norm = validate_and_normalize_address(tx.from_address, canon_chain)
            t_norm = validate_and_normalize_address(tx.to_address, canon_chain)
            if (
                f_norm.is_valid
                and t_norm.is_valid
                and f_norm.normalized_address == t_norm.normalized_address
            ):
                warnings.append("Self-transfer observed (from_address == to_address)")

        if tx.amount is None:
            missing_mandatory.append("amount")
            parsed_amount = None
        else:
            parsed_amount = _to_decimal(tx.amount)
            if parsed_amount is None:
                failed_reasons.append(f"Non-numeric or non-finite amount '{tx.amount}'")
            elif parsed_amount < Decimal("0"):
                failed_reasons.append(f"Negative transaction amount '{parsed_amount}' is invalid")

        if tx.decimals is not None and (tx.decimals < 0 or tx.decimals > 36):
            failed_reasons.append(f"Token decimals '{tx.decimals}' out of valid range [0, 36]")

        if tx.raw_amount is not None:
            raw_dec = _to_decimal(tx.raw_amount)
            if raw_dec is None or raw_dec < Decimal("0") or raw_dec != raw_dec.to_integral_value():
                failed_reasons.append(f"Invalid integer raw_amount '{tx.raw_amount}'")
            elif parsed_amount is not None and tx.decimals is not None and 0 <= tx.decimals <= 36:
                expected_raw = (parsed_amount * (Decimal(10) ** tx.decimals)).normalize()
                if expected_raw != raw_dec.normalize():
                    failed_reasons.append(
                        f"Amount/decimal inconsistency: amount={parsed_amount} with decimals={tx.decimals} "
                        f"yields raw={expected_raw}, but raw_amount={raw_dec}"
                    )

        if tx.token_contract:
            if canon_chain in _VALID_NETWORKS_BY_CHAIN:
                tok_val = validate_and_normalize_address(tx.token_contract, canon_chain)
                if not tok_val.is_valid:
                    failed_reasons.append(f"Invalid token_contract address: {tok_val.reason}")
                else:
                    for spec in self.thresholds.canonical_tokens:
                        if (
                            spec.chain == canon_chain
                            and spec.contract_address.lower() == tok_val.normalized_address.lower()
                        ):
                            if tx.decimals is not None and tx.decimals != spec.decimals:
                                failed_reasons.append(
                                    f"Token decimal mismatch for canonical {spec.symbol}: "
                                    f"observed={tx.decimals}, canonical={spec.decimals}"
                                )
                            if (
                                tx.asset_symbol
                                and tx.asset_symbol.strip().upper() != spec.symbol.upper()
                            ):
                                failed_reasons.append(
                                    f"Token symbol mismatch for canonical contract {spec.contract_address}: "
                                    f"observed='{tx.asset_symbol}', canonical='{spec.symbol}'"
                                )
        elif tx.transfer_type in (TransferType.ERC20, TransferType.SPL, TransferType.TRC20):
            warnings.append(
                f"Token transfer of type '{tx.transfer_type.value}' is missing token_contract identifier"
            )

        if tx.block_number is not None and tx.block_number < 0:
            failed_reasons.append(f"Negative block_number '{tx.block_number}' is invalid")
        if tx.block_hash and canon_chain in _VALID_NETWORKS_BY_CHAIN:
            ok_bh, bh_err = validate_tx_hash_format(tx.block_hash, canon_chain)
            if not ok_bh:
                failed_reasons.append(f"Invalid block_hash format: {bh_err}")

        if tx.confirmations is not None and tx.confirmations < 0:
            failed_reasons.append(f"Negative confirmations count '{tx.confirmations}' is invalid")

        status_norm = (tx.status or "").strip().lower()
        if status_norm in {"reorged", "dropped", "orphaned", "reverted_reorg"}:
            warnings.append(f"Transaction reports unstable chain state '{tx.status}'")
        if status_norm == "confirmed" and tx.confirmations == 0:
            failed_reasons.append(
                "Confirmation state contradiction: status='confirmed' with confirmations=0"
            )
        elif status_norm == "confirmed" and tx.block_number is None:
            warnings.append("Confirmed transaction is missing block_number")
        if status_norm == "pending" and tx.confirmations is not None and tx.confirmations > 0:
            failed_reasons.append(
                f"Confirmation state contradiction: status='pending' with confirmations={tx.confirmations}"
            )

        if tx.timestamp is not None:
            ts_utc = tx.timestamp if tx.timestamp.tzinfo else tx.timestamp.replace(tzinfo=UTC)
            if ts_utc.year < self.thresholds.min_valid_block_year:
                failed_reasons.append(
                    f"Timestamp '{ts_utc.isoformat()}' precedes blockchain genesis era ({self.thresholds.min_valid_block_year})"
                )
            now = utc_now()
            if (ts_utc - now).total_seconds() > self.thresholds.max_future_timestamp_skew_seconds:
                failed_reasons.append(
                    f"Timestamp '{ts_utc.isoformat()}' is abnormally far in the future"
                )
        else:
            warnings.append("Transaction timestamp is missing")

        all_observations: list[ProviderObservation] = list(provider_observations or [])
        if tx.tx_hash and canon_chain in _VALID_NETWORKS_BY_CHAIN and self.independent_providers:
            for prov in self.independent_providers:
                try:
                    obs = prov.fetch_transaction(canon_chain, tx.tx_hash)
                    if obs is not None:
                        all_observations.append(obs)
                except Exception as exc:
                    warnings.append(
                        f"Independent provider '{prov.provider_name}' raised lookup error: {type(exc).__name__}"
                    )

        conflicts, indep_status, prov_warnings = self._evaluate_provider_observations(
            primary=tx,
            canon_chain=canon_chain,
            observations=all_observations,
        )
        warnings.extend(prov_warnings)

        if conflicts:
            val_status = ValidationStatus.CONFLICTING
        elif failed_reasons:
            val_status = ValidationStatus.INVALID
        elif missing_mandatory:
            val_status = ValidationStatus.INCOMPLETE
        elif strict_indep and indep_status != IndependentVerificationStatus.VERIFIED_AGREE:
            val_status = ValidationStatus.UNVERIFIED
        else:
            val_status = ValidationStatus.VALID

        if missing_mandatory:
            failed_reasons.append(
                "Missing mandatory transaction fields: " + ", ".join(missing_mandatory)
            )

        findings: list[SecurityFinding] = []
        if val_status in (
            ValidationStatus.INVALID,
            ValidationStatus.CONFLICTING,
            ValidationStatus.INCOMPLETE,
        ):
            severity = (
                Severity.HIGH
                if val_status in (ValidationStatus.INVALID, ValidationStatus.CONFLICTING)
                else Severity.MEDIUM
            )
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.BLOCKCHAIN_DATA_INTEGRITY,
                    finding_type=f"blockchain_validation_{val_status.value.lower()}",
                    severity=severity,
                    confidence=0.95
                    if val_status in (ValidationStatus.INVALID, ValidationStatus.CONFLICTING)
                    else 0.80,
                    epistemic_label=EpistemicLabel.VERIFIED_FACT,
                    description=(
                        f"Blockchain data validation returned '{val_status.value}' for tx "
                        f"'{tx.tx_hash or 'unknown'}' on chain '{tx.chain or 'unknown'}'."
                    ),
                    source_address=tx.from_address,
                    evidence_references=[
                        EvidenceReference(
                            ref_type="transaction",
                            ref_id=tx.tx_hash or "missing-tx-hash",
                            chain=canon_chain or None,
                            provider=tx.source_provider,
                        )
                    ],
                    supporting_transaction_refs=[tx.tx_hash] if tx.tx_hash else [],
                    detection_source="blockchain_data_validator",
                    validation_status=val_status,
                    explanation=(
                        (
                            "; ".join(failed_reasons)
                            if failed_reasons
                            else "Provider conflict detected"
                        )
                        + (f". Conflicts: {conflicts}" if conflicts else "")
                    ),
                    limitations=[
                        "Validation checks internal consistency and configured provider consensus; single compromised upstream indexers cannot be detected without genuinely independent node RPCs."
                    ],
                    recommended_action=(
                        "Quarantine unverified or conflicting records and re-query an independent archival blockchain node."
                    ),
                    metadata={
                        "independent_verification_status": indep_status.value,
                        "data_quality_warnings": warnings,
                        "conflicts": conflicts,
                    },
                )
            )

        return BlockchainValidationReport(
            validation_status=val_status,
            independent_verification_status=indep_status,
            data_quality_warnings=warnings,
            failed_reasons=failed_reasons,
            conflicts=conflicts,
            source_provider=tx.source_provider,
            original_evidence_ref=tx.provenance_id or tx.tx_hash,
            findings=findings,
        )

    def validate_batch(
        self,
        investigation_id: str,
        transactions: list[TransactionRecord],
    ) -> list[BlockchainValidationReport]:
        """Validate a batch of transactions while detecting duplicate or conflicting entries."""
        reports: list[BlockchainValidationReport] = []
        seen: dict[tuple[str, str, int | None, int | None, str | None, str | None], TransactionRecord] = {}

        for tx in transactions:
            report = self.validate_transaction(investigation_id=investigation_id, tx=tx)
            key = (
                normalize_chain_name(tx.chain),
                (tx.tx_hash or "").strip().lower(),
                tx.log_index,
                tx.vout,
                (tx.from_address or "").strip().lower() if tx.transfer_type == TransferType.UTXO else None,
                (tx.to_address or "").strip().lower() if tx.transfer_type == TransferType.UTXO else None,
            )
            if key[1]:
                if key in seen:
                    prev = seen[key]
                    diff_fields: list[str] = []
                    if (prev.from_address or "").lower() != (tx.from_address or "").lower():
                        diff_fields.append("from_address")
                    if (prev.to_address or "").lower() != (tx.to_address or "").lower():
                        diff_fields.append("to_address")
                    if _to_decimal(prev.amount) != _to_decimal(tx.amount):
                        diff_fields.append("amount")
                    if prev.block_number != tx.block_number:
                        diff_fields.append("block_number")
                    if diff_fields:
                        report.validation_status = ValidationStatus.CONFLICTING
                        report.conflicts.append(
                            {
                                "type": "duplicate_batch_conflict",
                                "tx_hash": tx.tx_hash,
                                "differing_fields": diff_fields,
                            }
                        )
                        report.failed_reasons.append(
                            f"Duplicate tx_hash '{tx.tx_hash}' in batch with conflicting fields: {diff_fields}"
                        )
                    else:
                        report.data_quality_warnings.append(
                            f"Duplicate transaction '{tx.tx_hash}' observed in batch"
                        )
                else:
                    seen[key] = tx
            reports.append(report)

        return reports

    def _evaluate_provider_observations(
        self,
        primary: TransactionRecord,
        canon_chain: str,
        observations: list[ProviderObservation],
    ) -> tuple[list[dict[str, Any]], IndependentVerificationStatus, list[str]]:
        if not observations:
            return [], IndependentVerificationStatus.UNVERIFIED, []

        warnings: list[str] = []
        conflicts: list[dict[str, Any]] = []

        valid_obs: list[tuple[str, str, dict[str, Any]]] = []
        if primary.source_provider:
            valid_obs.append(
                (
                    primary.source_provider.strip(),
                    primary.source_provider.strip().lower(),
                    {
                        "chain": canon_chain,
                        "tx_hash": (primary.tx_hash or "").strip().lower(),
                        "from_address": primary.from_address,
                        "to_address": primary.to_address,
                        "amount": _to_decimal(primary.amount),
                        "block_number": primary.block_number,
                        "status": (primary.status or "").strip().lower() or None,
                        "token_contract": (primary.token_contract or "").strip().lower() or None,
                        "decimals": primary.decimals,
                    },
                )
            )

        for obs in observations:
            if obs.error:
                warnings.append(f"Provider '{obs.provider_name}' error: {obs.error}")
                continue
            if not obs.transaction:
                warnings.append(
                    f"Provider '{obs.provider_name}' returned empty transaction payload"
                )
                continue

            tx_data = obs.transaction
            obs_chain = normalize_chain_name(str(tx_data.get("chain") or canon_chain))
            upstream = (obs.upstream_source or obs.provider_name).strip().lower()
            valid_obs.append(
                (
                    obs.provider_name.strip(),
                    upstream,
                    {
                        "chain": obs_chain,
                        "tx_hash": str(tx_data.get("tx_hash") or "").strip().lower(),
                        "from_address": tx_data.get("from_address"),
                        "to_address": tx_data.get("to_address"),
                        "amount": _to_decimal(tx_data.get("amount")),
                        "block_number": tx_data.get("block_number"),
                        "status": str(tx_data.get("status")).strip().lower()
                        if tx_data.get("status")
                        else None,
                        "token_contract": str(tx_data.get("token_contract")).strip().lower()
                        if tx_data.get("token_contract")
                        else None,
                        "decimals": tx_data.get("decimals"),
                    },
                )
            )

        if len(valid_obs) < 2:
            return [], IndependentVerificationStatus.UNVERIFIED, warnings

        baseline_name, _, base = valid_obs[0]
        for prov_name, _, candidate in valid_obs[1:]:
            for field_name in (
                "chain",
                "tx_hash",
                "block_number",
                "status",
                "token_contract",
                "decimals",
            ):
                b_val = base.get(field_name)
                c_val = candidate.get(field_name)
                if b_val is not None and c_val is not None and b_val != c_val:
                    conflicts.append(
                        {
                            "field": field_name,
                            "provider_a": baseline_name,
                            "value_a": str(b_val),
                            "provider_b": prov_name,
                            "value_b": str(c_val),
                        }
                    )
            for addr_field in ("from_address", "to_address"):
                b_raw = base.get(addr_field)
                c_raw = candidate.get(addr_field)
                if b_raw and c_raw:
                    b_norm = validate_and_normalize_address(str(b_raw), canon_chain)
                    c_norm = validate_and_normalize_address(str(c_raw), canon_chain)
                    b_cmp = (
                        b_norm.normalized_address if b_norm.is_valid else str(b_raw).strip().lower()
                    )
                    c_cmp = (
                        c_norm.normalized_address if c_norm.is_valid else str(c_raw).strip().lower()
                    )
                    if b_cmp != c_cmp:
                        conflicts.append(
                            {
                                "field": addr_field,
                                "provider_a": baseline_name,
                                "value_a": str(b_raw),
                                "provider_b": prov_name,
                                "value_b": str(c_raw),
                            }
                        )
            b_amt = base.get("amount")
            c_amt = candidate.get("amount")
            if b_amt is not None and c_amt is not None and b_amt != c_amt:
                conflicts.append(
                    {
                        "field": "amount",
                        "provider_a": baseline_name,
                        "value_a": str(b_amt),
                        "provider_b": prov_name,
                        "value_b": str(c_amt),
                    }
                )

        if conflicts:
            return conflicts, IndependentVerificationStatus.VERIFIED_CONFLICT, warnings

        distinct_upstreams = {upstream for _, upstream, _ in valid_obs}
        if len(distinct_upstreams) < 2:
            warnings.append(
                "Multiple provider responses share the same underlying upstream data source "
                f"({sorted(distinct_upstreams)}); not treated as independent verification."
            )
            return [], IndependentVerificationStatus.NOT_INDEPENDENT, warnings

        return [], IndependentVerificationStatus.VERIFIED_AGREE, warnings


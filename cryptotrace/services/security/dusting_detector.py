"""Asset-aware dusting attack detection engine with false-positive suppression."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from statistics import median

from cryptotrace.schemas.findings import SecurityFinding
from cryptotrace.schemas.security_common import (
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    Severity,
    ValidationStatus,
)
from cryptotrace.schemas.security_inputs import TransactionRecord
from cryptotrace.services.security.address_similarity import (
    normalize_chain_name,
    validate_and_normalize_address,
)
from cryptotrace.services.security.security_config import DetectionThresholds, DustThresholdRule


def _to_decimal(val: object) -> Decimal | None:
    if val is None:
        return None
    try:
        dec = Decimal(str(val))
        return dec if dec.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


class DustingDetector:
    """Detects suspicious asset-aware dusting patterns while filtering ordinary small transfers."""

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.thresholds = thresholds or DetectionThresholds()

    def resolve_threshold(self, tx: TransactionRecord) -> tuple[DustThresholdRule, str]:
        """Resolve asset-, chain-, contract-, and decimal-specific dust threshold."""
        chain = normalize_chain_name(tx.chain)
        contract = (tx.token_contract or "").strip().lower()
        symbol = (tx.asset_symbol or "").strip().upper()
        ttype = tx.transfer_type.value

        if contract and (chain, contract) in self.thresholds.contract_dust_overrides:
            return (
                self.thresholds.contract_dust_overrides[(chain, contract)],
                f"contract_override:{chain}:{contract}",
            )

        exact_key = f"{chain}:{ttype}:{symbol}"
        if exact_key in self.thresholds.dust_rules:
            return self.thresholds.dust_rules[exact_key], f"asset_rule:{exact_key}"

        if tx.decimals is not None and tx.decimals >= 0:
            scale_exp = min(tx.decimals, self.thresholds.default_token_dust_decimals_scale)
            fallback_max = Decimal("0.01") if scale_exp >= 2 else Decimal(10) ** (-scale_exp)
            return (
                DustThresholdRule(max_amount=fallback_max),
                f"decimal_fallback:decimals={tx.decimals}",
            )

        native_defaults = {
            "bitcoin": Decimal("0.00001"),
            "ethereum": Decimal("0.0001"),
            "solana": Decimal("0.001"),
            "tron": Decimal("0.1"),
        }
        return (
            DustThresholdRule(max_amount=native_defaults.get(chain, Decimal("0.0001"))),
            f"chain_fallback:{chain}",
        )

    def analyze(
        self,
        investigation_id: str,
        transactions: list[TransactionRecord],
        known_exchange_addresses: set[str] | None = None,
    ) -> list[SecurityFinding]:
        """Analyze transactions for dusting sprays or repeated unsolicited dust deposits."""
        exchange_set = {addr.strip().lower() for addr in (known_exchange_addresses or set())}

        asset_amounts_by_wallet: dict[tuple[str, str, str], list[Decimal]] = defaultdict(list)
        small_txs_by_sender_asset: dict[
            tuple[str, str, str], list[tuple[TransactionRecord, DustThresholdRule, str]]
        ] = defaultdict(list)
        small_txs_by_target_asset: dict[
            tuple[str, str, str], list[tuple[TransactionRecord, DustThresholdRule, str]]
        ] = defaultdict(list)

        for tx in transactions:
            chain = normalize_chain_name(tx.chain)
            amt = _to_decimal(tx.amount)
            if not chain or amt is None or amt <= Decimal("0"):
                continue

            symbol = (tx.asset_symbol or "UNKNOWN").strip().upper()
            contract = (tx.token_contract or "").strip().lower()
            asset_key = f"{tx.transfer_type.value}:{contract or symbol}"

            from_val = validate_and_normalize_address(tx.from_address or "", chain)
            to_val = validate_and_normalize_address(tx.to_address or "", chain)
            if not from_val.is_valid or not to_val.is_valid:
                continue

            sender = from_val.normalized_address
            target = to_val.normalized_address
            asset_amounts_by_wallet[(chain, asset_key, target)].append(amt)

            if tx.is_exchange_transfer or sender.lower() in exchange_set:
                continue
            if tx.is_airdrop_claim:
                continue

            rule, rule_source = self.resolve_threshold(tx)
            if amt <= rule.max_amount:
                small_txs_by_sender_asset[(chain, asset_key, sender)].append(
                    (tx, rule, rule_source)
                )
                small_txs_by_target_asset[(chain, asset_key, target)].append(
                    (tx, rule, rule_source)
                )

        findings: list[SecurityFinding] = []
        reported_tx_sets: set[frozenset[str]] = set()

        for (chain, asset_key, sender), items in small_txs_by_sender_asset.items():
            rule = items[0][1]
            rule_source = items[0][2]
            txs = [item[0] for item in items]
            unique_targets = {
                validate_and_normalize_address(t.to_address or "", chain).normalized_address
                for t in txs
                if t.to_address
            }
            timestamps = sorted(t.timestamp.timestamp() for t in txs if t.timestamp is not None)
            within_burst = (
                len(timestamps) >= rule.min_repeat_count
                and (timestamps[-1] - timestamps[0]) <= rule.burst_window_seconds
            )
            is_spray = len(unique_targets) >= rule.spray_unique_targets
            is_repeated_to_same = len(txs) >= rule.min_repeat_count and len(unique_targets) <= 2

            if not (
                is_spray
                or (is_repeated_to_same and within_burst)
                or len(txs) >= rule.min_repeat_count + 1
            ):
                continue

            tx_refs = [t.tx_hash for t in txs if t.tx_hash]
            sig_key = frozenset(tx_refs or [f"{sender}:{len(txs)}"])
            reported_tx_sets.add(sig_key)

            reasons: list[str] = [
                f"{len(txs)} tiny transfer(s) <= {rule.max_amount} ({rule_source})"
            ]
            if is_spray:
                reasons.append(
                    f"fanned out across {len(unique_targets)} distinct recipient wallets"
                )
            if within_burst:
                reasons.append("compressed burst timing")
            if is_repeated_to_same:
                reasons.append("repeated micro-deposits to same recipient(s)")

            confidence = 0.62
            if is_spray:
                confidence += 0.20
            if within_burst:
                confidence += 0.10
            if len(txs) >= 5:
                confidence += 0.05
            confidence = round(min(confidence, 0.96), 4)

            severity = Severity.HIGH if (is_spray and within_burst) else Severity.MEDIUM
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.DUSTING_ATTACK,
                    finding_type="dusting_spray_or_repeat_pattern",
                    severity=severity,
                    confidence=confidence,
                    epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                    description=(
                        f"Potential dusting activity on '{chain}' ({asset_key}) originating from '{sender}'."
                    ),
                    source_address=sender,
                    evidence_references=[
                        EvidenceReference(ref_type="address", ref_id=sender, chain=chain)
                    ]
                    + [
                        EvidenceReference(ref_type="transaction", ref_id=h, chain=chain)
                        for h in tx_refs
                    ],
                    supporting_transaction_refs=tx_refs,
                    detection_source="dusting_detector",
                    validation_status=ValidationStatus.VALID
                    if tx_refs
                    else ValidationStatus.UNVERIFIED,
                    explanation="Flagged because " + "; ".join(reasons) + ".",
                    limitations=[
                        "Micro-value transfers can also result from promotional drops, fee-rebate bots, or test payouts if not labeled upstream.",
                        "Confidence depends on completeness of wallet transaction history and asset threshold configuration.",
                    ],
                    recommended_action=(
                        "Isolate these dust UTXOs/inputs in clustering heuristics and verify whether target wallets later co-spent them."
                    ),
                    metadata={
                        "chain": chain,
                        "asset_key": asset_key,
                        "threshold_amount": str(rule.max_amount),
                        "threshold_source": rule_source,
                        "tx_count": len(txs),
                        "unique_targets": len(unique_targets),
                        "within_burst_window": within_burst,
                    },
                )
            )

        for (chain, asset_key, target), items in small_txs_by_target_asset.items():
            rule = items[0][1]
            rule_source = items[0][2]
            txs = [item[0] for item in items]
            tx_refs = [t.tx_hash for t in txs if t.tx_hash]
            if frozenset(tx_refs) in reported_tx_sets or len(txs) < rule.min_repeat_count:
                continue

            wallet_vals = sorted(asset_amounts_by_wallet[(chain, asset_key, target)])
            wallet_median = Decimal(str(median(wallet_vals))) if wallet_vals else Decimal("0")
            if (
                wallet_median > Decimal("0")
                and wallet_median <= rule.max_amount * Decimal("10")
                and all(
                    (_to_decimal(t.amount) or Decimal("0"))
                    > (wallet_median * self.thresholds.dust_ordinary_ratio_to_median)
                    for t in txs
                )
            ):
                continue

            unique_senders = {
                validate_and_normalize_address(t.from_address or "", chain).normalized_address
                for t in txs
                if t.from_address
            }
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.DUSTING_ATTACK,
                    finding_type="repeated_target_dust_deposits",
                    severity=Severity.MEDIUM,
                    confidence=0.68,
                    epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                    description=(
                        f"Wallet '{target}' received {len(txs)} abnormally small '{asset_key}' deposits on '{chain}'."
                    ),
                    source_address=target,
                    evidence_references=[
                        EvidenceReference(ref_type="address", ref_id=target, chain=chain)
                    ]
                    + [
                        EvidenceReference(ref_type="transaction", ref_id=h, chain=chain)
                        for h in tx_refs
                    ],
                    supporting_transaction_refs=tx_refs,
                    detection_source="dusting_detector",
                    validation_status=ValidationStatus.VALID
                    if tx_refs
                    else ValidationStatus.UNVERIFIED,
                    explanation=(
                        f"Detected {len(txs)} deposits <= {rule.max_amount} ({rule_source}) across "
                        f"{len(unique_senders)} sender(s), significantly below wallet baseline."
                    ),
                    limitations=[
                        "Repeated small payouts from unlabeled faucets, staking rewards, or merchants can resemble dusting."
                    ],
                    recommended_action=(
                        "Check sender clustering and avoid treating unspent dust inputs as strong ownership proof without co-spend evidence."
                    ),
                    metadata={
                        "chain": chain,
                        "asset_key": asset_key,
                        "threshold_amount": str(rule.max_amount),
                        "threshold_source": rule_source,
                        "wallet_median_amount": str(wallet_median),
                        "tx_count": len(txs),
                        "unique_senders": len(unique_senders),
                    },
                )
            )

        return findings

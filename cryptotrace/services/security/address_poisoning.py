"""Contextual address poisoning and look-alike wallet detection engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

from cryptotrace.schemas.findings import SecurityFinding
from cryptotrace.schemas.security_common import (
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    Severity,
    ValidationStatus,
)
from cryptotrace.schemas.security_inputs import AddressContext, TransactionRecord
from cryptotrace.services.security.address_similarity import (
    AddressSimilarityAnalyzer,
    inspect_text_confusables,
    normalize_chain_name,
    validate_and_normalize_address,
)
from cryptotrace.services.security.security_config import DetectionThresholds


def _to_decimal(val: object) -> Decimal | None:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _sort_key_ts(tx: TransactionRecord) -> float:
    if tx.timestamp is None:
        return 0.0
    return tx.timestamp.timestamp()


class AddressPoisoningDetector:
    """Detects address poisoning and deceptive look-alike wallet patterns with contextual correlation."""

    def __init__(
        self,
        thresholds: DetectionThresholds | None = None,
        similarity_analyzer: AddressSimilarityAnalyzer | None = None,
    ) -> None:
        self.thresholds = thresholds or DetectionThresholds()
        self.similarity = similarity_analyzer or AddressSimilarityAnalyzer(self.thresholds)

    def analyze(
        self,
        investigation_id: str,
        target_wallet: str,
        chain: str,
        transactions: list[TransactionRecord],
        known_counterparties: list[AddressContext] | None = None,
        report_uncorroborated_lookalikes: bool = False,
    ) -> list[SecurityFinding]:
        """Analyze transactions around target_wallet for poisoning and look-alike substitutions."""
        canon_chain = normalize_chain_name(chain)
        target_val = validate_and_normalize_address(target_wallet, canon_chain)
        if not target_val.is_valid:
            return []

        target_norm = target_val.normalized_address
        counterparty_map: dict[str, AddressContext] = {}
        for ctx in known_counterparties or []:
            ctx_val = validate_and_normalize_address(ctx.address, normalize_chain_name(ctx.chain))
            if ctx_val.is_valid and ctx_val.chain == canon_chain:
                counterparty_map[ctx_val.normalized_address] = ctx

        ordered_txs = sorted(
            [t for t in transactions if normalize_chain_name(t.chain) == canon_chain],
            key=_sort_key_ts,
        )

        counterparty_txs: dict[str, list[TransactionRecord]] = defaultdict(list)
        first_seen_ts: dict[str, datetime | None] = {}
        for tx in ordered_txs:
            from_val = (
                validate_and_normalize_address(tx.from_address, canon_chain)
                if tx.from_address
                else None
            )
            to_val = (
                validate_and_normalize_address(tx.to_address, canon_chain)
                if tx.to_address
                else None
            )
            if not from_val or not to_val or not from_val.is_valid or not to_val.is_valid:
                continue
            other = None
            if (
                from_val.normalized_address == target_norm
                and to_val.normalized_address != target_norm
            ):
                other = to_val.normalized_address
            elif (
                to_val.normalized_address == target_norm
                and from_val.normalized_address != target_norm
            ):
                other = from_val.normalized_address
            if other is None:
                continue
            counterparty_txs[other].append(tx)
            if other not in first_seen_ts:
                first_seen_ts[other] = tx.timestamp

        established_refs: dict[str, AddressContext | None] = {}
        for addr, ctx in counterparty_map.items():
            if addr != target_norm and (ctx.is_known_counterparty or ctx.interaction_count >= 2):
                established_refs[addr] = ctx

        for addr, txs in counterparty_txs.items():
            if addr in established_refs:
                continue
            meaningful = [
                t
                for t in txs
                if (_to_decimal(t.amount) or Decimal("0"))
                > self.thresholds.poisoning_decoy_max_amount
            ]
            if meaningful:
                established_refs[addr] = counterparty_map.get(addr)

        findings: list[SecurityFinding] = []
        seen_pairs: set[tuple[str, str]] = set()

        for addr, ctx in counterparty_map.items():
            if ctx.label:
                conf = inspect_text_confusables(ctx.label)
                if conf["has_invisible_or_bidi"] or (
                    conf["has_confusables"] and conf["mixed_scripts"]
                ):
                    findings.append(
                        SecurityFinding(
                            investigation_id=investigation_id,
                            finding_category=FindingCategory.LOOKALIKE_WALLET,
                            finding_type="homoglyph_wallet_label",
                            severity=Severity.MEDIUM,
                            confidence=0.82,
                            epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                            description=(
                                f"Wallet label '{ctx.label}' contains invisible characters or cross-script homoglyphs."
                            ),
                            source_address=target_norm,
                            suspected_lookalike_address=addr,
                            evidence_references=[
                                EvidenceReference(
                                    ref_type="address",
                                    ref_id=addr,
                                    chain=canon_chain,
                                    detail=f"Label inspection: {conf}",
                                )
                            ],
                            detection_source="address_poisoning_detector",
                            validation_status=ValidationStatus.VALID,
                            explanation=(
                                "Detected non-ASCII confusable or invisible Unicode characters in the wallet label, "
                                "which is a common visual impersonation technique."
                            ),
                            limitations=[
                                "Label metadata comes from off-chain naming services or local annotations and may have legitimate international characters."
                            ],
                            recommended_action=(
                                "Verify the canonical wallet address directly rather than relying on the rendered label."
                            ),
                            metadata={"label_inspection": conf},
                        )
                    )

        for cand_addr, cand_txs in counterparty_txs.items():
            cand_ctx = counterparty_map.get(cand_addr)
            cand_is_established = (
                cand_ctx is not None
                and (cand_ctx.is_known_counterparty or cand_ctx.interaction_count >= 3)
                and all(
                    (_to_decimal(t.amount) or Decimal("0"))
                    > self.thresholds.poisoning_decoy_max_amount
                    for t in cand_txs
                )
            )
            if cand_is_established:
                continue

            for ref_addr in established_refs:
                if ref_addr == cand_addr or (ref_addr, cand_addr) in seen_pairs:
                    continue

                sim = self.similarity.compare(
                    reference_address=ref_addr,
                    candidate_address=cand_addr,
                    reference_chain=canon_chain,
                    candidate_chain=canon_chain,
                )
                if not sim.is_suspicious_lookalike:
                    continue

                seen_pairs.add((ref_addr, cand_addr))

                decoy_txs = [
                    t
                    for t in cand_txs
                    if Decimal("0")
                    <= (_to_decimal(t.amount) or Decimal("0"))
                    <= self.thresholds.poisoning_decoy_max_amount
                ]
                ref_txs = counterparty_txs.get(ref_addr, [])
                ref_first = first_seen_ts.get(ref_addr)
                cand_first = first_seen_ts.get(cand_addr)

                appeared_after_ref = bool(
                    ref_first is not None and cand_first is not None and cand_first >= ref_first
                )
                if cand_addr not in counterparty_map and ref_addr in counterparty_map:
                    ref_ctx = counterparty_map[ref_addr]
                    if ref_ctx.first_seen and cand_first and cand_first >= ref_ctx.first_seen:
                        appeared_after_ref = True

                outgoing_to_cand_after_decoy = False
                if decoy_txs:
                    first_decoy_ts = min(_sort_key_ts(t) for t in decoy_txs)
                    for t in cand_txs:
                        amt = _to_decimal(t.amount) or Decimal("0")
                        from_norm = (
                            validate_and_normalize_address(
                                t.from_address, canon_chain
                            ).normalized_address
                            if t.from_address
                            else ""
                        )
                        if (
                            from_norm == target_norm
                            and amt > self.thresholds.poisoning_decoy_max_amount
                            and _sort_key_ts(t) >= first_decoy_ts
                        ):
                            outgoing_to_cand_after_decoy = True
                            break

                repeated_decoy = (
                    len(decoy_txs) >= self.thresholds.poisoning_repeat_appearance_threshold
                )
                has_decoy_value = len(decoy_txs) > 0
                is_vanity_bookend = "VANITY_PREFIX_SUFFIX_BOOKEND" in sim.pattern_flags
                is_low_edit = "LOW_EDIT_DISTANCE_SUBSTITUTION" in sim.pattern_flags

                contextual_signals: list[str] = []
                if has_decoy_value:
                    contextual_signals.append("zero_or_micro_value_decoy_transfer")
                if appeared_after_ref:
                    contextual_signals.append("appeared_after_legitimate_counterparty")
                if repeated_decoy:
                    contextual_signals.append("repeated_decoy_appearances")
                if outgoing_to_cand_after_decoy:
                    contextual_signals.append("subsequent_outbound_transfer_to_lookalike")
                if is_vanity_bookend:
                    contextual_signals.append("prefix_suffix_vanity_bookend")
                if is_low_edit:
                    contextual_signals.append("low_edit_distance_character_substitution")

                poisoning_evidence_present = (
                    has_decoy_value
                    or outgoing_to_cand_after_decoy
                    or (
                        appeared_after_ref
                        and (repeated_decoy or is_vanity_bookend)
                        and len(cand_txs) <= 3
                    )
                )

                tx_refs = [t.tx_hash for t in cand_txs if t.tx_hash]
                ev_refs = [
                    EvidenceReference(
                        ref_type="address",
                        ref_id=cand_addr,
                        chain=canon_chain,
                        detail=f"Compared against established counterparty {ref_addr}",
                    )
                ] + [
                    EvidenceReference(
                        ref_type="transaction",
                        ref_id=h,
                        chain=canon_chain,
                    )
                    for h in tx_refs
                ]

                if poisoning_evidence_present:
                    confidence = 0.55
                    if has_decoy_value:
                        confidence += 0.18
                    if appeared_after_ref:
                        confidence += 0.10
                    if is_vanity_bookend:
                        confidence += 0.08
                    if repeated_decoy:
                        confidence += 0.06
                    if outgoing_to_cand_after_decoy:
                        confidence = max(confidence + 0.12, 0.90)
                    confidence = round(min(confidence, 0.98), 4)

                    severity = Severity.HIGH
                    if outgoing_to_cand_after_decoy:
                        severity = Severity.CRITICAL
                    elif not has_decoy_value and len(contextual_signals) <= 2:
                        severity = Severity.MEDIUM

                    findings.append(
                        SecurityFinding(
                            investigation_id=investigation_id,
                            finding_category=FindingCategory.ADDRESS_POISONING,
                            finding_type="address_poisoning_lookalike",
                            severity=severity,
                            confidence=confidence,
                            epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                            description=(
                                f"Suspected address poisoning: address '{cand_addr}' closely resembles "
                                f"counterparty '{ref_addr}' with contextual decoy indicators."
                            ),
                            source_address=ref_addr,
                            suspected_lookalike_address=cand_addr,
                            similarity_score=sim.combined_similarity,
                            evidence_references=ev_refs,
                            supporting_transaction_refs=tx_refs,
                            detection_source="address_poisoning_detector",
                            validation_status=ValidationStatus.VALID
                            if tx_refs
                            else ValidationStatus.UNVERIFIED,
                            explanation=(
                                f"{sim.explanation} Correlated contextual indicators: "
                                f"{', '.join(contextual_signals)}."
                            ),
                            limitations=[
                                "Address similarity plus small transfers is a strong behavioral indicator, not cryptographic proof of attacker intent.",
                                "Vanity addresses can occasionally occur legitimately for branded services or wallets.",
                            ],
                            recommended_action=(
                                "Highlight the full middle characters of both addresses, cross-check out-of-band counterparty ownership, "
                                "and avoid copying recipient addresses from recent transaction history."
                            ),
                            metadata={
                                "prefix_match_len": sim.prefix_match_len,
                                "suffix_match_len": sim.suffix_match_len,
                                "levenshtein_similarity": sim.levenshtein_similarity,
                                "vanity_pattern_score": sim.vanity_pattern_score,
                                "pattern_flags": list(sim.pattern_flags),
                                "contextual_signals": contextual_signals,
                                "decoy_tx_count": len(decoy_txs),
                                "reference_tx_count": len(ref_txs),
                            },
                        )
                    )
                elif report_uncorroborated_lookalikes:
                    findings.append(
                        SecurityFinding(
                            investigation_id=investigation_id,
                            finding_category=FindingCategory.LOOKALIKE_WALLET,
                            finding_type="uncorroborated_similar_address",
                            severity=Severity.INFO,
                            confidence=round(min(0.45, sim.combined_similarity * 0.5), 4),
                            epistemic_label=EpistemicLabel.UNVERIFIED_OBSERVATION,
                            description=(
                                f"Informational look-alike observation: '{cand_addr}' shares character similarity "
                                f"with '{ref_addr}' without poisoning transfer indicators."
                            ),
                            source_address=ref_addr,
                            suspected_lookalike_address=cand_addr,
                            similarity_score=sim.combined_similarity,
                            evidence_references=ev_refs,
                            supporting_transaction_refs=tx_refs,
                            detection_source="address_poisoning_detector",
                            validation_status=ValidationStatus.VALID
                            if tx_refs
                            else ValidationStatus.UNVERIFIED,
                            explanation=(
                                f"{sim.explanation} No zero/micro-value decoy or substitution chronology was found, "
                                "so this is NOT classified as address poisoning."
                            ),
                            limitations=[
                                "Similarity alone never proves malicious poisoning; legitimate wallets can share prefix/suffix characters by chance or vanity generation."
                            ],
                            recommended_action=(
                                "No poisoning accusation warranted; verify address ownership normally if needed."
                            ),
                            metadata={
                                "pattern_flags": list(sim.pattern_flags),
                                "contextual_signals": contextual_signals,
                            },
                        )
                    )

        return findings

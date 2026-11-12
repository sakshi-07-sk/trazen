"""Contract-first token impersonation and metadata tampering detector."""

from __future__ import annotations

import re

from rapidfuzz.distance import Levenshtein

from cryptotrace.schemas.findings import SecurityFinding
from cryptotrace.schemas.security_common import (
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    Severity,
    ValidationStatus,
)
from cryptotrace.schemas.security_inputs import TokenMetadataInput
from cryptotrace.services.security.address_similarity import (
    AddressSimilarityAnalyzer,
    inspect_text_confusables,
    normalize_chain_name,
    validate_and_normalize_address,
)
from cryptotrace.services.security.security_config import CanonicalTokenSpec, DetectionThresholds

_ALNUM_CLEAN_RE = re.compile(r"[^a-z0-9]")


def _fold_token_text(value: str | None) -> str:
    if not value:
        return ""
    conf = inspect_text_confusables(value)
    skeleton = str(conf["skeleton"]).lower().strip()
    return _ALNUM_CLEAN_RE.sub("", skeleton)


class TokenImpersonationDetector:
    """Detects fake symbols, homoglyph spoofing, contract-chain mismatches, and metadata drift."""

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
        token: TokenMetadataInput,
    ) -> list[SecurityFinding]:
        """Inspect token metadata using (chain, contract_address) as primary identity."""
        chain = normalize_chain_name(token.chain)
        contract_raw = (token.contract_address or "").strip()
        contract_val = validate_and_normalize_address(contract_raw, chain) if contract_raw else None
        contract_norm = (
            contract_val.normalized_address
            if (contract_val and contract_val.is_valid)
            else contract_raw.lower()
        )

        findings: list[SecurityFinding] = []
        ev_refs = [
            EvidenceReference(
                ref_type="token_contract",
                ref_id=contract_norm or (token.symbol or "unknown-token"),
                chain=chain or None,
                provider=token.source_provider,
            )
        ]

        if contract_raw and contract_val is not None and not contract_val.is_valid:
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.TOKEN_IMPERSONATION,
                    finding_type="invalid_token_contract_for_chain",
                    severity=Severity.HIGH,
                    confidence=0.90,
                    epistemic_label=EpistemicLabel.VERIFIED_FACT,
                    description=(
                        f"Token contract '{contract_raw}' is not valid for chain '{chain}'."
                    ),
                    source_address=contract_raw,
                    evidence_references=ev_refs,
                    detection_source="token_impersonation_detector",
                    validation_status=ValidationStatus.INVALID,
                    explanation=contract_val.reason or "Contract format failed chain validation.",
                    limitations=[
                        "Assumes the declared chain identifier reflects the intended ledger."
                    ],
                    recommended_action="Reject or quarantine this token metadata until chain and contract are verified.",
                )
            )

        for field_label, text_val in (("symbol", token.symbol), ("name", token.name)):
            if not text_val:
                continue
            conf = inspect_text_confusables(text_val)
            if conf["has_invisible_or_bidi"] or (
                conf["has_confusables"]
                and (conf["mixed_scripts"] or bool(conf["confusable_codepoints"]))
            ):
                findings.append(
                    SecurityFinding(
                        investigation_id=investigation_id,
                        finding_category=FindingCategory.TOKEN_IMPERSONATION,
                        finding_type=f"homoglyph_or_invisible_token_{field_label}",
                        severity=Severity.HIGH,
                        confidence=0.92,
                        epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                        description=(
                            f"Token {field_label} '{text_val}' contains invisible/bidi or cross-script homoglyph characters."
                        ),
                        source_address=contract_norm or None,
                        evidence_references=ev_refs,
                        detection_source="token_impersonation_detector",
                        validation_status=ValidationStatus.VALID,
                        explanation=(
                            f"Unicode inspection detected confusable/invisible characters in token {field_label}: "
                            f"invisible={conf['invisible_codepoints']}, confusables={conf['confusable_codepoints']}, "
                            f"skeleton='{conf['skeleton']}'."
                        ),
                        limitations=[
                            "Certain international projects use non-ASCII glyphs legitimately, though ticker symbols mixing scripts are strongly deceptive."
                        ],
                        recommended_action=(
                            "Identify the token exclusively by verified (chain, contract_address) and display raw Unicode warnings to analysts."
                        ),
                        metadata={"field": field_label, "unicode_inspection": conf},
                    )
                )

        drift_fields: list[str] = []
        if token.previous_symbol and token.symbol and token.previous_symbol != token.symbol:
            drift_fields.append(f"symbol: '{token.previous_symbol}' -> '{token.symbol}'")
        if token.previous_name and token.name and token.previous_name != token.name:
            drift_fields.append(f"name: '{token.previous_name}' -> '{token.name}'")
        if (
            token.previous_decimals is not None
            and token.decimals is not None
            and token.previous_decimals != token.decimals
        ):
            drift_fields.append(f"decimals: {token.previous_decimals} -> {token.decimals}")

        if drift_fields:
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.TOKEN_IMPERSONATION,
                    finding_type="suspicious_token_metadata_change",
                    severity=Severity.HIGH,
                    confidence=0.86,
                    epistemic_label=EpistemicLabel.VERIFIED_FACT,
                    description=(
                        f"Token metadata for contract '{contract_norm or 'unknown'}' changed unexpectedly: "
                        + "; ".join(drift_fields)
                    ),
                    source_address=contract_norm or None,
                    evidence_references=ev_refs,
                    detection_source="token_impersonation_detector",
                    validation_status=ValidationStatus.VALID,
                    explanation=(
                        "Standard immutable token contracts rarely alter symbol, name, or decimals after deployment; "
                        "changes indicate upgradeable spoofing, off-chain metadata poisoning, or inconsistent providers."
                    ),
                    limitations=[
                        "Proxy contracts or indexer re-indexing corrections can occasionally update metadata."
                    ],
                    recommended_action="Verify on-chain contract state and compare historical ABI getter responses.",
                    metadata={"changed_fields": drift_fields},
                )
            )

        same_chain_canonicals: list[CanonicalTokenSpec] = [
            spec for spec in self.thresholds.canonical_tokens if spec.chain == chain
        ]
        exact_canonical: CanonicalTokenSpec | None = next(
            (
                spec
                for spec in same_chain_canonicals
                if spec.contract_address.lower() == contract_norm.lower()
            ),
            None,
        )

        if exact_canonical is not None:
            inconsistencies: list[str] = []
            if token.decimals is not None and token.decimals != exact_canonical.decimals:
                inconsistencies.append(
                    f"decimals={token.decimals} != canonical {exact_canonical.decimals}"
                )
            if token.symbol and token.symbol.strip().upper() != exact_canonical.symbol.upper():
                inconsistencies.append(
                    f"symbol='{token.symbol}' != canonical '{exact_canonical.symbol}'"
                )
            if inconsistencies:
                findings.append(
                    SecurityFinding(
                        investigation_id=investigation_id,
                        finding_category=FindingCategory.TOKEN_IMPERSONATION,
                        finding_type="canonical_contract_metadata_mismatch",
                        severity=Severity.HIGH,
                        confidence=0.91,
                        epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                        description=(
                            f"Metadata for canonical contract '{contract_norm}' conflicts with verified registry."
                        ),
                        source_address=contract_norm,
                        evidence_references=ev_refs,
                        detection_source="token_impersonation_detector",
                        validation_status=ValidationStatus.CONFLICTING,
                        explanation="Mismatch against verified registry: "
                        + "; ".join(inconsistencies),
                        limitations=[
                            "Provider indexing corruption could also cause mismatched token metadata."
                        ],
                        recommended_action="Cross-check token metadata against an independent RPC node.",
                        metadata={"inconsistencies": inconsistencies},
                    )
                )
            return findings

        cross_chain_match = next(
            (
                spec
                for spec in self.thresholds.canonical_tokens
                if spec.chain != chain and spec.contract_address.lower() == contract_norm.lower()
            ),
            None,
        )
        if cross_chain_match is not None and contract_norm:
            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.TOKEN_IMPERSONATION,
                    finding_type="cross_chain_contract_mismatch",
                    severity=Severity.HIGH,
                    confidence=0.90,
                    epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                    description=(
                        f"Contract '{contract_norm}' is the canonical '{cross_chain_match.symbol}' on "
                        f"'{cross_chain_match.chain}', not '{chain}'."
                    ),
                    source_address=contract_norm,
                    evidence_references=ev_refs,
                    detection_source="token_impersonation_detector",
                    validation_status=ValidationStatus.CONFLICTING,
                    explanation=(
                        "Using a canonical contract address from another chain indicates chain mislabeling or "
                        "cross-chain impersonation."
                    ),
                    limitations=[
                        "Custom bridged deployments on deterministic addresses can rarely match across EVM chains."
                    ],
                    recommended_action="Verify canonical deployment chain and contract bytecode independently.",
                    metadata={
                        "canonical_chain": cross_chain_match.chain,
                        "canonical_symbol": cross_chain_match.symbol,
                    },
                )
            )

        folded_symbol = _fold_token_text(token.symbol)
        folded_name = _fold_token_text(token.name)

        for spec in same_chain_canonicals:
            spec_sym = _fold_token_text(spec.symbol)
            spec_name = _fold_token_text(spec.name)

            sym_exact_collision = bool(folded_symbol and folded_symbol == spec_sym)
            sym_sim = (
                float(Levenshtein.normalized_similarity(folded_symbol, spec_sym))
                if folded_symbol and spec_sym
                else 0.0
            )
            name_sim = (
                float(Levenshtein.normalized_similarity(folded_name, spec_name))
                if folded_name and spec_name
                else 0.0
            )

            contract_lookalike = False
            contract_sim_score = 0.0
            if contract_val and contract_val.is_valid:
                sim_res = self.similarity.compare(
                    reference_address=spec.contract_address,
                    candidate_address=contract_norm,
                    reference_chain=chain,
                    candidate_chain=chain,
                )
                contract_lookalike = sim_res.is_suspicious_lookalike
                contract_sim_score = sim_res.combined_similarity

            is_impersonation = (
                sym_exact_collision
                or name_sim >= self.thresholds.token_name_similarity_threshold
                or contract_lookalike
                or (sym_sim >= 0.75 and len(folded_symbol) >= 3)
            )
            if not is_impersonation:
                continue

            reasons: list[str] = []
            if sym_exact_collision:
                reasons.append(
                    f"symbol skeleton '{folded_symbol}' matches canonical '{spec.symbol}' at a different contract '{contract_norm or 'missing'}'"
                )
            elif sym_sim >= 0.75:
                reasons.append(
                    f"symbol '{token.symbol}' is visually/lexically similar ({sym_sim:.2f}) to canonical '{spec.symbol}'"
                )
            if name_sim >= self.thresholds.token_name_similarity_threshold:
                reasons.append(
                    f"token name '{token.name}' resembles canonical '{spec.name}' (similarity {name_sim:.2f})"
                )
            if contract_lookalike:
                reasons.append(
                    f"contract address '{contract_norm}' resembles canonical contract '{spec.contract_address}' ({contract_sim_score:.2f})"
                )
            if token.decimals is not None and token.decimals != spec.decimals:
                reasons.append(
                    f"decimals ({token.decimals}) differ from canonical '{spec.symbol}' decimals ({spec.decimals})"
                )

            confidence = 0.72
            if sym_exact_collision:
                confidence += 0.14
            if name_sim >= self.thresholds.token_name_similarity_threshold:
                confidence += 0.06
            if contract_lookalike:
                confidence += 0.08
            confidence = round(min(confidence, 0.96), 4)

            findings.append(
                SecurityFinding(
                    investigation_id=investigation_id,
                    finding_category=FindingCategory.TOKEN_IMPERSONATION,
                    finding_type="suspected_token_impersonation",
                    severity=Severity.HIGH
                    if (sym_exact_collision or contract_lookalike)
                    else Severity.MEDIUM,
                    confidence=confidence,
                    epistemic_label=EpistemicLabel.SUSPICIOUS_INDICATOR,
                    description=(
                        f"Suspected impersonation of '{spec.symbol}' ({spec.name}) on '{chain}' by non-canonical "
                        f"contract '{contract_norm or 'unspecified'}'."
                    ),
                    source_address=contract_norm or None,
                    suspected_lookalike_address=spec.contract_address
                    if contract_lookalike
                    else None,
                    similarity_score=round(max(sym_sim, name_sim, contract_sim_score), 4),
                    evidence_references=ev_refs
                    + [
                        EvidenceReference(
                            ref_type="token_contract",
                            ref_id=spec.contract_address,
                            chain=chain,
                            detail=f"Canonical {spec.symbol} ({spec.name})",
                        )
                    ],
                    detection_source="token_impersonation_detector",
                    validation_status=ValidationStatus.VALID
                    if contract_norm
                    else ValidationStatus.INCOMPLETE,
                    explanation=(
                        "Primary token identity relies on (chain, contract_address), not ticker symbol. "
                        + "; ".join(reasons)
                        + "."
                    ),
                    limitations=[
                        "Unlisted legitimate bridged or wrapped tokens can share ticker symbols with canonical assets.",
                        "Canonical registry coverage determines which baseline assets are matched automatically.",
                    ],
                    recommended_action=(
                        f"Do not treat symbol '{token.symbol or ''}' as proof of authenticity; verify canonical contract "
                        f"'{spec.contract_address}' on-chain."
                    ),
                    metadata={
                        "canonical_contract": spec.contract_address,
                        "canonical_symbol": spec.symbol,
                        "symbol_similarity": round(sym_sim, 4),
                        "name_similarity": round(name_sim, 4),
                        "contract_lookalike": contract_lookalike,
                    },
                )
            )
            break

        return findings

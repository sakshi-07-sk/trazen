"""Chain-aware wallet address validation, normalization, and similarity analysis."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz.distance import Levenshtein

from cryptotrace.schemas.security_common import EVM_CHAINS, ChainId
from cryptotrace.services.security.security_config import DetectionThresholds

_EVM_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_BASE58_RE = re.compile(r"^[13][1-9A-HJ-NP-Za-km-z]{25,34}$")
_BTC_BECH32_RE = re.compile(r"^(bc1|BC1)[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{11,71}$")
_SOL_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_TRON_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {ch: idx for idx, ch in enumerate(_BASE58_ALPHABET)}

_INVISIBLE_OR_BIDI_CHARS: frozenset[str] = frozenset(
    {
        "\u200b",  # zero-width space
        "\u200c",  # zero-width non-joiner
        "\u200d",  # zero-width joiner
        "\u200e",  # left-to-right mark
        "\u200f",  # right-to-left mark
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",  # right-to-left override
        "\u2060",  # word joiner
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
        "\ufeff",  # BOM / ZWNBSP
    }
)

# Common cross-script confusables seen in ENS/wallet label and token spoofing
CONFUSABLE_CHAR_MAP: dict[str, str] = {
    "\u0410": "A",  # Cyrillic А
    "\u0430": "a",  # Cyrillic а
    "\u0412": "B",  # Cyrillic В
    "\u0421": "C",  # Cyrillic С
    "\u0441": "c",  # Cyrillic с
    "\u0415": "E",  # Cyrillic Е
    "\u0435": "e",  # Cyrillic е
    "\u041d": "H",  # Cyrillic Н
    "\u0406": "I",  # Cyrillic І
    "\u0456": "i",  # Cyrillic і
    "\u041a": "K",  # Cyrillic К
    "\u041c": "M",  # Cyrillic М
    "\u041e": "O",  # Cyrillic О
    "\u043e": "o",  # Cyrillic о
    "\u0420": "P",  # Cyrillic Р
    "\u0440": "p",  # Cyrillic р
    "\u0422": "T",  # Cyrillic Т
    "\u0425": "X",  # Cyrillic Х
    "\u0445": "x",  # Cyrillic х
    "\u0443": "y",  # Cyrillic у
    "\u0391": "A",  # Greek Α
    "\u0392": "B",  # Greek Β
    "\u0395": "E",  # Greek Ε
    "\u039f": "O",  # Greek Ο
    "\u03bf": "o",  # Greek ο
    "\u03a1": "P",  # Greek Ρ
    "\u03a4": "T",  # Greek Τ
    "\u0399": "I",  # Greek Ι
    "\u039a": "K",  # Greek Κ
    "\u039c": "M",  # Greek Μ
    "\u039d": "N",  # Greek Ν
    "\u0396": "Z",  # Greek Ζ
    "\u03a7": "X",  # Greek Χ
    "\u03b1": "a",  # Greek α
    "\u03c1": "p",  # Greek ρ
}


def _decode_base58check(address: str) -> tuple[bool, str | None]:
    """Decode Base58 string and verify 4-byte double-SHA256 checksum."""
    num = 0
    for ch in address:
        if ch not in _BASE58_INDEX:
            return False, "Non-Base58 character encountered"
        num = num * 58 + _BASE58_INDEX[ch]

    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num > 0 else b""
    leading_zeros = len(address) - len(address.lstrip("1"))
    decoded = (b"\x00" * leading_zeros) + raw
    if len(decoded) < 5:
        return False, "Decoded Base58Check payload is too short"

    payload, checksum = decoded[:-4], decoded[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        return False, "Base58Check checksum mismatch"
    return True, None


def inspect_text_confusables(text: str) -> dict[str, object]:
    """Detect invisible/bidi characters and non-ASCII homoglyphs in labels or metadata."""
    invisible_found = sorted({ch for ch in text if ch in _INVISIBLE_OR_BIDI_CHARS})
    confusable_found = sorted({ch for ch in text if ch in CONFUSABLE_CHAR_MAP})
    nfkc = unicodedata.normalize("NFKC", text)
    skeleton_chars: list[str] = []
    for ch in nfkc:
        if ch in _INVISIBLE_OR_BIDI_CHARS:
            continue
        skeleton_chars.append(CONFUSABLE_CHAR_MAP.get(ch, ch))
    skeleton = "".join(skeleton_chars)
    scripts = {
        unicodedata.name(ch, "UNKNOWN").split()[0]
        for ch in text
        if ch.isalpha() and ch not in _INVISIBLE_OR_BIDI_CHARS
    }
    return {
        "has_invisible_or_bidi": bool(invisible_found),
        "invisible_codepoints": [f"U+{ord(c):04X}" for c in invisible_found],
        "has_confusables": bool(confusable_found),
        "confusable_codepoints": [f"U+{ord(c):04X}" for c in confusable_found],
        "mixed_scripts": len(scripts) > 1,
        "scripts": sorted(scripts),
        "skeleton": skeleton,
    }


@dataclass(frozen=True)
class AddressValidationResult:
    """Result of chain-specific wallet/contract address validation and normalization."""

    raw_address: str
    chain: str
    is_valid: bool
    normalized_address: str
    comparison_body: str
    address_format: str
    checksum_status: str
    reason: str | None = None


@dataclass(frozen=True)
class AddressSimilarityResult:
    """Explainable address similarity breakdown between two validated addresses."""

    chain: str
    reference_address: str
    candidate_address: str
    is_exact_match: bool
    compatible_chains: bool
    prefix_match_len: int
    suffix_match_len: int
    prefix_similarity: float
    suffix_similarity: float
    levenshtein_similarity: float
    vanity_pattern_score: float
    combined_similarity: float
    is_suspicious_lookalike: bool
    pattern_flags: tuple[str, ...]
    explanation: str


def normalize_chain_name(chain: str | None) -> str:
    """Normalize common chain aliases into canonical lowercase identifiers."""
    if not chain:
        return ""
    cleaned = chain.strip().lower()
    aliases = {
        "eth": ChainId.ETHEREUM.value,
        "eth-mainnet": ChainId.ETHEREUM.value,
        "eth-sepolia": ChainId.ETHEREUM.value,
        "1": ChainId.ETHEREUM.value,
        "mainnet": ChainId.ETHEREUM.value,
        "matic": ChainId.POLYGON.value,
        "bnb": ChainId.BSC.value,
        "binance": ChainId.BSC.value,
        "arb": ChainId.ARBITRUM.value,
        "op": ChainId.OPTIMISM.value,
        "avax": ChainId.AVALANCHE.value,
        "btc": ChainId.BITCOIN.value,
        "btc-mainnet": ChainId.BITCOIN.value,
        "btc-testnet": ChainId.BITCOIN.value,
        "sol": ChainId.SOLANA.value,
        "trx": ChainId.TRON.value,
    }
    return aliases.get(cleaned, cleaned)


def validate_and_normalize_address(address: str, chain: str) -> AddressValidationResult:
    """Validate syntax/checksum and produce canonical normalized form for a specific chain."""
    raw = address.strip()
    canon_chain = normalize_chain_name(chain)

    if not raw:
        return AddressValidationResult(
            raw_address=address,
            chain=canon_chain,
            is_valid=False,
            normalized_address="",
            comparison_body="",
            address_format="empty",
            checksum_status="invalid",
            reason="Address is empty",
        )

    if canon_chain in EVM_CHAINS:
        if not _EVM_RE.match(raw):
            return AddressValidationResult(
                raw_address=address,
                chain=canon_chain,
                is_valid=False,
                normalized_address="",
                comparison_body="",
                address_format="evm_hex",
                checksum_status="invalid",
                reason="Invalid EVM address format (expected 0x + 40 hex chars)",
            )
        hex_body = raw[2:]
        is_mixed_case = not (hex_body.islower() or hex_body.isupper())
        return AddressValidationResult(
            raw_address=address,
            chain=canon_chain,
            is_valid=True,
            normalized_address=raw.lower(),
            comparison_body=hex_body.lower(),
            address_format="evm_hex",
            checksum_status="mixed_case_unverified" if is_mixed_case else "not_applicable",
            reason=None,
        )

    if canon_chain == ChainId.BITCOIN.value:
        if _BTC_BECH32_RE.match(raw):
            is_mixed = not (raw.islower() or raw.isupper())
            if is_mixed:
                return AddressValidationResult(
                    raw_address=address,
                    chain=canon_chain,
                    is_valid=False,
                    normalized_address="",
                    comparison_body="",
                    address_format="btc_bech32",
                    checksum_status="invalid",
                    reason="Mixed-case Bech32 Bitcoin address violates BIP-173/350",
                )
            norm = raw.lower()
            return AddressValidationResult(
                raw_address=address,
                chain=canon_chain,
                is_valid=True,
                normalized_address=norm,
                comparison_body=norm[3:],
                address_format="btc_bech32",
                checksum_status="format_valid",
                reason=None,
            )
        if _BTC_BASE58_RE.match(raw):
            ok, err = _decode_base58check(raw)
            return AddressValidationResult(
                raw_address=address,
                chain=canon_chain,
                is_valid=ok,
                normalized_address=raw if ok else "",
                comparison_body=raw[1:] if ok else "",
                address_format="btc_base58check",
                checksum_status="valid" if ok else "invalid",
                reason=err,
            )
        return AddressValidationResult(
            raw_address=address,
            chain=canon_chain,
            is_valid=False,
            normalized_address="",
            comparison_body="",
            address_format="btc_unknown",
            checksum_status="invalid",
            reason="Invalid Bitcoin address format",
        )

    if canon_chain == ChainId.SOLANA.value:
        if not _SOL_RE.match(raw):
            return AddressValidationResult(
                raw_address=address,
                chain=canon_chain,
                is_valid=False,
                normalized_address="",
                comparison_body="",
                address_format="solana_base58",
                checksum_status="invalid",
                reason="Invalid Solana Base58 address format",
            )
        return AddressValidationResult(
            raw_address=address,
            chain=canon_chain,
            is_valid=True,
            normalized_address=raw,
            comparison_body=raw,
            address_format="solana_base58",
            checksum_status="not_applicable",
            reason=None,
        )

    if canon_chain == ChainId.TRON.value:
        if not _TRON_RE.match(raw):
            return AddressValidationResult(
                raw_address=address,
                chain=canon_chain,
                is_valid=False,
                normalized_address="",
                comparison_body="",
                address_format="tron_base58check",
                checksum_status="invalid",
                reason="Invalid TRON address format (expected T + 33 Base58 chars)",
            )
        ok, err = _decode_base58check(raw)
        return AddressValidationResult(
            raw_address=address,
            chain=canon_chain,
            is_valid=ok,
            normalized_address=raw if ok else "",
            comparison_body=raw[1:] if ok else "",
            address_format="tron_base58check",
            checksum_status="valid" if ok else "invalid",
            reason=err,
        )

    return AddressValidationResult(
        raw_address=address,
        chain=canon_chain,
        is_valid=False,
        normalized_address="",
        comparison_body="",
        address_format="unsupported",
        checksum_status="invalid",
        reason=f"Unsupported blockchain identifier '{chain}'",
    )


def _common_prefix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    count = 0
    while count < limit and a[count] == b[count]:
        count += 1
    return count


def _common_suffix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    count = 0
    while count < limit and a[-1 - count] == b[-1 - count]:
        count += 1
    return count


class AddressSimilarityAnalyzer:
    """Configurable look-alike address analysis engine."""

    def __init__(self, thresholds: DetectionThresholds | None = None) -> None:
        self.thresholds = thresholds or DetectionThresholds()

    def compare(
        self,
        reference_address: str,
        candidate_address: str,
        reference_chain: str,
        candidate_chain: str | None = None,
        allow_cross_evm: bool = False,
    ) -> AddressSimilarityResult:
        """Compare two addresses with chain-awareness, returning multi-metric similarity."""
        ref_chain = normalize_chain_name(reference_chain)
        cand_chain = normalize_chain_name(candidate_chain or reference_chain)

        same_chain = ref_chain == cand_chain
        both_evm = ref_chain in EVM_CHAINS and cand_chain in EVM_CHAINS
        if not same_chain and not (allow_cross_evm and both_evm):
            return AddressSimilarityResult(
                chain=ref_chain,
                reference_address=reference_address,
                candidate_address=candidate_address,
                is_exact_match=False,
                compatible_chains=False,
                prefix_match_len=0,
                suffix_match_len=0,
                prefix_similarity=0.0,
                suffix_similarity=0.0,
                levenshtein_similarity=0.0,
                vanity_pattern_score=0.0,
                combined_similarity=0.0,
                is_suspicious_lookalike=False,
                pattern_flags=("INCOMPATIBLE_CHAINS",),
                explanation=(
                    f"Skipped similarity comparison between incompatible chains "
                    f"'{ref_chain}' and '{cand_chain}'."
                ),
            )

        ref_val = validate_and_normalize_address(reference_address, ref_chain)
        cand_val = validate_and_normalize_address(candidate_address, cand_chain)
        if not ref_val.is_valid or not cand_val.is_valid:
            reasons = [r for r in (ref_val.reason, cand_val.reason) if r]
            return AddressSimilarityResult(
                chain=ref_chain,
                reference_address=reference_address,
                candidate_address=candidate_address,
                is_exact_match=False,
                compatible_chains=True,
                prefix_match_len=0,
                suffix_match_len=0,
                prefix_similarity=0.0,
                suffix_similarity=0.0,
                levenshtein_similarity=0.0,
                vanity_pattern_score=0.0,
                combined_similarity=0.0,
                is_suspicious_lookalike=False,
                pattern_flags=("INVALID_ADDRESS_FORMAT",),
                explanation="Cannot compare invalid addresses: " + "; ".join(reasons),
            )

        body_a = ref_val.comparison_body
        body_b = cand_val.comparison_body

        if ref_val.normalized_address == cand_val.normalized_address:
            return AddressSimilarityResult(
                chain=ref_chain,
                reference_address=ref_val.normalized_address,
                candidate_address=cand_val.normalized_address,
                is_exact_match=True,
                compatible_chains=True,
                prefix_match_len=len(body_a),
                suffix_match_len=len(body_a),
                prefix_similarity=1.0,
                suffix_similarity=1.0,
                levenshtein_similarity=1.0,
                vanity_pattern_score=0.0,
                combined_similarity=1.0,
                is_suspicious_lookalike=False,
                pattern_flags=("EXACT_MATCH",),
                explanation="Addresses normalize to the exact same canonical address.",
            )

        prefix_len = _common_prefix_len(body_a, body_b)
        suffix_len = _common_suffix_len(body_a, body_b)
        min_len = max(min(len(body_a), len(body_b)), 1)

        anchor_scale = 6.0
        prefix_sim = round(min(prefix_len / anchor_scale, 1.0), 4)
        suffix_sim = round(min(suffix_len / anchor_scale, 1.0), 4)
        lev_sim = round(float(Levenshtein.normalized_similarity(body_a, body_b)), 4)

        flags: list[str] = []
        if not same_chain and both_evm:
            flags.append("CROSS_EVM_COMPARISON")
        if prefix_len >= self.thresholds.min_prefix_match_chars:
            flags.append("HIGH_PREFIX_SIMILARITY")
        if suffix_len >= self.thresholds.min_suffix_match_chars:
            flags.append("HIGH_SUFFIX_SIMILARITY")
        if (
            prefix_len >= self.thresholds.min_prefix_match_chars
            and suffix_len >= self.thresholds.min_suffix_match_chars
        ):
            flags.append("VANITY_PREFIX_SUFFIX_BOOKEND")
        if lev_sim >= self.thresholds.min_levenshtein_similarity:
            flags.append("HIGH_LEVENSHTEIN_SIMILARITY")

        vanity_score = 0.0
        if prefix_len >= 3 and suffix_len >= 3:
            vanity_score = round(min(1.0, (prefix_sim * 0.5) + (suffix_sim * 0.5)), 4)
        elif prefix_len >= 5 or suffix_len >= 5:
            vanity_score = round(max(prefix_sim, suffix_sim) * 0.75, 4)

        combined = round(max(lev_sim, vanity_score), 4)
        is_lookalike = (
            (
                prefix_len >= self.thresholds.min_prefix_match_chars
                and suffix_len >= self.thresholds.min_suffix_match_chars
            )
            or lev_sim >= self.thresholds.min_levenshtein_similarity
            or combined >= self.thresholds.min_combined_similarity
        )

        edit_dist = Levenshtein.distance(body_a, body_b)
        if 1 <= edit_dist <= 4:
            flags.append("LOW_EDIT_DISTANCE_SUBSTITUTION")
            is_lookalike = True
            combined = max(combined, round(1.0 - (edit_dist / min_len), 4))

        explanation = (
            f"Normalized comparison on '{ref_chain}' found {prefix_len} matching prefix char(s), "
            f"{suffix_len} matching suffix char(s), and normalized Levenshtein similarity {lev_sim:.2f}."
        )
        return AddressSimilarityResult(
            chain=ref_chain,
            reference_address=ref_val.normalized_address,
            candidate_address=cand_val.normalized_address,
            is_exact_match=False,
            compatible_chains=True,
            prefix_match_len=prefix_len,
            suffix_match_len=suffix_len,
            prefix_similarity=prefix_sim,
            suffix_similarity=suffix_sim,
            levenshtein_similarity=lev_sim,
            vanity_pattern_score=vanity_score,
            combined_similarity=combined,
            is_suspicious_lookalike=is_lookalike,
            pattern_flags=tuple(flags),
            explanation=explanation,
        )


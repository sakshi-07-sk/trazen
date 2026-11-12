"""Unit tests for chain-aware address validation, normalization, and similarity analysis."""

from __future__ import annotations

import hashlib

import pytest

from cryptotrace.services.security.address_similarity import (
    AddressSimilarityAnalyzer,
    inspect_text_confusables,
    validate_and_normalize_address,
)

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _make_base58check(version_byte: bytes, payload20: bytes) -> str:
    body = version_byte + payload20
    chk = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    raw = body + chk
    num = int.from_bytes(raw, "big")
    chars: list[str] = []
    while num > 0:
        num, rem = divmod(num, 58)
        chars.append(_B58[rem])
    leading_ones = len(raw) - len(raw.lstrip(b"\x00"))
    return ("1" * leading_ones) + "".join(reversed(chars))


@pytest.mark.unit
def test_chain_specific_address_validation_and_normalization() -> None:
    evm = validate_and_normalize_address("0xAbCdEf1234567890aBcDeF1234567890AbCdEf12", "ethereum")
    assert evm.is_valid
    assert evm.normalized_address == "0xabcdef1234567890abcdef1234567890abcdef12"

    btc_p2pkh = _make_base58check(b"\x00", b"\x11" * 20)
    btc_res = validate_and_normalize_address(btc_p2pkh, "bitcoin")
    assert btc_res.is_valid
    assert btc_res.checksum_status == "valid"

    corrupt_btc = btc_p2pkh[:-1] + ("2" if btc_p2pkh[-1] != "2" else "3")
    btc_bad = validate_and_normalize_address(corrupt_btc, "bitcoin")
    assert not btc_bad.is_valid
    assert btc_bad.checksum_status == "invalid"

    bech_bad = validate_and_normalize_address(
        "bc1Qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "bitcoin"
    )
    assert not bech_bad.is_valid

    sol_addr = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol_res = validate_and_normalize_address(sol_addr, "solana")
    assert sol_res.is_valid
    assert sol_res.normalized_address == sol_addr


@pytest.mark.unit
def test_incompatible_chain_comparison_is_rejected() -> None:
    analyzer = AddressSimilarityAnalyzer()
    btc_addr = _make_base58check(b"\x00", b"\x22" * 20)
    eth_addr = "0x1111111111111111111111111111111111111111"

    result = analyzer.compare(
        reference_address=eth_addr,
        candidate_address=btc_addr,
        reference_chain="ethereum",
        candidate_chain="bitcoin",
    )
    assert not result.compatible_chains
    assert not result.is_suspicious_lookalike
    assert "INCOMPATIBLE_CHAINS" in result.pattern_flags


@pytest.mark.unit
def test_prefix_suffix_and_levenshtein_similarity_modes() -> None:
    analyzer = AddressSimilarityAnalyzer()
    ref = "0x1234567890abcdef1234567890abcdef1234abcd"

    vanity = "0x123456ffffffffffffffffffffffffff0000abcd"
    vanity_res = analyzer.compare(ref, vanity, "ethereum")
    assert vanity_res.prefix_match_len >= 6
    assert vanity_res.suffix_match_len >= 4
    assert vanity_res.is_suspicious_lookalike
    assert "VANITY_PREFIX_SUFFIX_BOOKEND" in vanity_res.pattern_flags

    one_char = "0x1234567890abcdef1234567890abcdef1234abce"
    char_res = analyzer.compare(ref, one_char, "ethereum")
    assert char_res.levenshtein_similarity > 0.95
    assert "LOW_EDIT_DISTANCE_SUBSTITUTION" in char_res.pattern_flags

    exact_upper = ref.upper().replace("0X", "0x")
    exact_res = analyzer.compare(ref, exact_upper, "ethereum")
    assert exact_res.is_exact_match
    assert not exact_res.is_suspicious_lookalike


@pytest.mark.unit
def test_unicode_homoglyph_and_bidi_inspection() -> None:
    spoof = inspect_text_confusables("V\u0430ult\u200bTreasury")
    assert spoof["has_invisible_or_bidi"]
    assert spoof["has_confusables"]
    assert spoof["mixed_scripts"]

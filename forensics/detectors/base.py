"""Shared helper utilities for forensic detectors."""

from __future__ import annotations

from typing import Iterable, List

from forensics.schemas.output import ForensicFinding, SeverityLevel


class FindingIdSequence:
    """Deterministic sequential finding ID generator (FT-0001, FT-0002, ...)."""

    def __init__(self, prefix: str = "FT", start: int = 1) -> None:
        self.prefix = prefix
        self._counter = start

    def next_id(self) -> str:
        fid = f"{self.prefix}-{self._counter:04d}"
        self._counter += 1
        return fid


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def make_finding(
    seq: FindingIdSequence,
    *,
    rule_id: str,
    rule_version: str,
    title: str,
    category: str,
    severity: SeverityLevel,
    confidence: float,
    explanation: str,
    evidence_refs: Iterable[str],
    limitations: Iterable[str],
    affected_addresses: Iterable[str] = (),
    relationship_status: str = "inferred",
    metadata: dict | None = None,
) -> ForensicFinding:
    return ForensicFinding(
        finding_id=seq.next_id(),
        rule_id=rule_id,
        rule_version=rule_version,
        title=title,
        category=category,
        severity=severity,
        confidence=round(clamp(confidence), 4),
        explanation=explanation,
        evidence_refs=dedupe_preserve_order(evidence_refs),
        limitations=list(limitations),
        affected_addresses=dedupe_preserve_order(affected_addresses),
        relationship_status=relationship_status,  # type: ignore[arg-type]
        metadata=metadata or {},
    )

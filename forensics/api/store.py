"""Pluggable investigation repository protocol and cached in-memory store."""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol

from forensics.datasets.fixtures import build_all_benchmark_scenarios, make_cross_case_shared_destination_cases
from forensics.engine import ForensicEngine
from forensics.schemas.input import InvestigationCase
from forensics.schemas.output import ForensicAnalysisBundle


class InvestigationRepository(Protocol):
    """Adapter interface that Role 1's graph/persistence layer can implement."""

    def get_case(self, investigation_id: str) -> Optional[InvestigationCase]:
        ...

    def save_case(self, case: InvestigationCase) -> None:
        ...

    def list_cases(self) -> List[InvestigationCase]:
        ...


class InMemoryInvestigationStore:
    """Thread-safe/deterministic in-memory store with per-investigation analysis cache."""

    def __init__(self, preload_demo_cases: bool = True) -> None:
        self._cases: Dict[str, InvestigationCase] = {}
        self._bundle_cache: Dict[str, ForensicAnalysisBundle] = {}
        if preload_demo_cases:
            for exp in build_all_benchmark_scenarios():
                self._cases[exp.case.investigation_id] = exp.case
            for case in make_cross_case_shared_destination_cases():
                self._cases[case.investigation_id] = case

    def get_case(self, investigation_id: str) -> Optional[InvestigationCase]:
        return self._cases.get(investigation_id)

    def save_case(self, case: InvestigationCase) -> None:
        self._cases[case.investigation_id] = case
        self._bundle_cache.pop(case.investigation_id, None)

    def list_cases(self) -> List[InvestigationCase]:
        return list(self._cases.values())

    def get_or_compute_analysis(
        self, investigation_id: str, engine: ForensicEngine
    ) -> Optional[ForensicAnalysisBundle]:
        cached = self._bundle_cache.get(investigation_id)
        if cached is not None:
            return cached
        case = self.get_case(investigation_id)
        if case is None:
            return None
        bundle = engine.analyze_case(case)
        self._bundle_cache[investigation_id] = bundle
        return bundle

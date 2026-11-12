"""Pluggable investigation repository protocol and bounded LRU in-memory store."""

from __future__ import annotations

from collections import OrderedDict
from typing import List, Optional, Protocol

from forensics.datasets.fixtures import (
    build_all_benchmark_scenarios,
    make_cross_case_shared_destination_cases,
)
from forensics.engine import ForensicEngine
from forensics.schemas.input import InvestigationCase
from forensics.schemas.output import ForensicAnalysisBundle


class CaseConflictError(Exception):
    """Raised when attempting to overwrite an existing investigation with different content."""


class InvestigationRepository(Protocol):
    """Adapter interface that Role 1's graph/persistence layer can implement."""

    def get_case(self, investigation_id: str) -> Optional[InvestigationCase]:
        ...

    def save_case(self, case: InvestigationCase) -> None:
        ...

    def list_cases(self) -> List[InvestigationCase]:
        ...


class InMemoryInvestigationStore:
    """Bounded LRU in-memory store (max 500 entries) with per-investigation analysis cache."""

    def __init__(self, preload_demo_cases: bool = True, max_entries: int = 500) -> None:
        self.max_entries = max_entries
        self._cases: OrderedDict[str, InvestigationCase] = OrderedDict()
        self._bundle_cache: OrderedDict[str, ForensicAnalysisBundle] = OrderedDict()
        if preload_demo_cases:
            for exp in build_all_benchmark_scenarios():
                self._cases[exp.case.investigation_id] = exp.case
            for case in make_cross_case_shared_destination_cases():
                self._cases[case.investigation_id] = case

    def get_case(self, investigation_id: str) -> Optional[InvestigationCase]:
        case = self._cases.get(investigation_id)
        if case is not None:
            self._cases.move_to_end(investigation_id)
        return case

    def save_case(self, case: InvestigationCase) -> None:
        existing = self._cases.get(case.investigation_id)
        if existing is not None:
            if existing.model_dump(mode="json") != case.model_dump(mode="json"):
                raise CaseConflictError(
                    f"Investigation '{case.investigation_id}' already exists with different data."
                )
            self._cases.move_to_end(case.investigation_id)
            return

        if len(self._cases) >= self.max_entries:
            evicted_id, _ = self._cases.popitem(last=False)
            self._bundle_cache.pop(evicted_id, None)

        self._cases[case.investigation_id] = case
        self._bundle_cache.pop(case.investigation_id, None)

    def list_cases(self) -> List[InvestigationCase]:
        return list(self._cases.values())

    def get_or_compute_analysis(
        self, investigation_id: str, engine: ForensicEngine
    ) -> Optional[ForensicAnalysisBundle]:
        cached = self._bundle_cache.get(investigation_id)
        if cached is not None:
            self._bundle_cache.move_to_end(investigation_id)
            if investigation_id in self._cases:
                self._cases.move_to_end(investigation_id)
            return cached

        case = self.get_case(investigation_id)
        if case is None:
            return None

        bundle = engine.analyze_case(case)
        if len(self._bundle_cache) >= self.max_entries:
            self._bundle_cache.popitem(last=False)
        self._bundle_cache[investigation_id] = bundle
        return bundle

"""Shared pytest fixtures for Role 2 Forensic Intelligence Engine tests."""

from __future__ import annotations

import pytest

from forensics.config import ForensicsConfig, load_config
from forensics.engine import ForensicEngine


@pytest.fixture(scope="session")
def config() -> ForensicsConfig:
    return load_config()


@pytest.fixture(scope="session")
def engine(config: ForensicsConfig) -> ForensicEngine:
    return ForensicEngine(config=config)

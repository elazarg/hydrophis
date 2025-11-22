"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def golden_outputs_dir() -> Path:
    """Return the golden outputs directory path."""
    return Path(__file__).parent / "golden_outputs"

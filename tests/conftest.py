"""Shared test fixtures for jostack-mdparse."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_md() -> Path:
    """Return path to the sample Markdown fixture."""
    return FIXTURES_DIR / "sample.md"


@pytest.fixture
def sample_content(sample_md: Path) -> str:
    """Return content of the sample Markdown fixture."""
    return sample_md.read_text(encoding="utf-8")

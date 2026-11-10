"""Shared test setup: make the project root importable and isolate the cache."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def clear_price_cache():
    """The price cache is process-global, so reset it around every test."""
    from data.price_data_loader import Cache

    Cache._price_cache.clear()
    yield
    Cache._price_cache.clear()


@pytest.fixture
def fake_prices(monkeypatch):
    """Patch the price fetcher so strategies run on a given DataFrame offline."""
    from strategies import strategy_abstract

    def _install(df: pd.DataFrame) -> None:
        monkeypatch.setattr(
            strategy_abstract.DataFetcher,
            "fetch_data",
            staticmethod(lambda tickers, start, end: df),
        )

    return _install

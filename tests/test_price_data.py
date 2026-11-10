"""Tests for price formatting and the in-memory cache (yfinance is mocked)."""

from __future__ import annotations

import pandas as pd
import pytest

from data import price_data_loader
from data.data_formatter import DataFormatter
from data.price_data_loader import PriceDataLoader

IDX = pd.date_range("2020-01-01", periods=2, freq="D")


def _yf_frame(tickers):
    """Mimic yfinance output with group_by='ticker' (MultiIndex columns)."""
    cols = pd.MultiIndex.from_product([tickers, ["Open", "Close"]])
    return pd.DataFrame(1.0, index=IDX, columns=cols)


def test_formatter_multi_ticker():
    out = DataFormatter.format_data(_yf_frame(["A", "B"]), ["A", "B", "MISSING"])
    assert set(out) == {"A", "B"}


def test_formatter_single_ticker_multiindex():
    # yfinance >= 0.2.48 keeps the ticker level even for one ticker.
    out = DataFormatter.format_data(_yf_frame(["A"]), ["A"])
    assert list(out) == ["A"]


def test_formatter_empty_download():
    assert DataFormatter.format_data(pd.DataFrame(), ["A"]) == {}


def test_formatter_single_ticker_flat_columns():
    raw = pd.DataFrame({"Open": [1, 2], "Close": [3, 4]}, index=IDX)
    out = DataFormatter.format_data(raw, ["A"])
    assert out["A"].tolist() == [3, 4]


@pytest.fixture
def download_calls(monkeypatch):
    calls = []

    def fake_download(tickers, start, end):
        calls.append(list(tickers))
        return _yf_frame(list(tickers))

    monkeypatch.setattr(price_data_loader.Downloader, "download", staticmethod(fake_download))
    return calls


def test_loader_caches_per_ticker_and_period(download_calls):
    PriceDataLoader.load(["A", "B"], "2020-01-01", "2020-01-02")
    df = PriceDataLoader.load(["A", "B", "C"], "2020-01-01", "2020-01-02")
    # Second call downloads only the ticker it has not seen yet.
    assert download_calls == [["A", "B"], ["C"]]
    assert list(df.columns) == ["A", "B", "C"]


def test_loader_different_period_is_a_cache_miss(download_calls):
    PriceDataLoader.load(["A"], "2020-01-01", "2020-01-02")
    PriceDataLoader.load(["A"], "2021-01-01", "2021-01-02")
    assert len(download_calls) == 2


def test_loader_empty_ticker_list(download_calls):
    assert PriceDataLoader.load([], "2020-01-01", "2020-01-02").empty
    assert download_calls == []

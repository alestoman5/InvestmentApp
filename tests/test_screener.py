"""Tests for StockScreener and CSVDataProvider."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from utils.data_provider import CSVDataProvider, DataProviderBase
from utils.screener import StockScreener


class FakeProvider(DataProviderBase):
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def get_data_for_quarter(self, quarter: str) -> pd.DataFrame:
        return self._df[self._df["quarter"] == quarter].reset_index(drop=True)

    def available_years(self) -> list[int]:
        return sorted({int(q[:4]) for q in self._df["quarter"]})


@pytest.fixture
def screener():
    df = pd.DataFrame(
        {
            "quarter": ["2015Q1"] * 4 + ["2016Q1"],
            "ticker": ["AAA", "BBB", "CCC", "DDD", "AAA"],
            "pe": [8.0, 15.0, 30.0, np.nan, 9.0],
            "debt_to_equity": [0.2, 1.5, 0.4, 0.1, 0.2],
        }
    )
    return StockScreener(FakeProvider(df))


def test_no_criteria_returns_whole_quarter(screener):
    assert screener.filter_stocks(2015, "Q1", {}) == ["AAA", "BBB", "CCC", "DDD"]


def test_under_and_over(screener):
    assert screener.filter_stocks(2015, "Q1", {"pe": ("Under", 20)}) == ["AAA", "BBB"]
    assert screener.filter_stocks(2015, "Q1", {"pe": ("Over", 20)}) == ["CCC"]


def test_criteria_are_combined_with_and(screener):
    crit = {"pe": ("Under", 20), "debt_to_equity": ("Under", 1)}
    assert screener.filter_stocks(2015, "Q1", crit) == ["AAA"]


def test_missing_values_never_pass_a_filter(screener):
    # DDD has no P/E, so it must drop out of both directions.
    assert "DDD" not in screener.filter_stocks(2015, "Q1", {"pe": ("Under", 1e9)})
    assert "DDD" not in screener.filter_stocks(2015, "Q1", {"pe": ("Over", -1e9)})


def test_unknown_metric_raises(screener):
    with pytest.raises(ValueError, match="not found"):
        screener.filter_stocks(2015, "Q1", {"nonexistent": ("Over", 1)})


def test_empty_quarter_returns_empty_list(screener):
    assert screener.filter_stocks(1999, "Q4", {"pe": ("Under", 10)}) == []


def test_available_years(screener):
    assert screener.available_years() == [2015, 2016]


def test_csv_provider(tmp_path):
    csv = tmp_path / "snp500.csv"
    pd.DataFrame(
        {"quarter": ["2010Q1", "2010Q2", "2011Q1"], "ticker": ["A", "B", "C"]}
    ).to_csv(csv, index=False)
    provider = CSVDataProvider(csv)
    assert provider.available_years() == [2010, 2011]
    assert provider.get_data_for_quarter("2010Q2")["ticker"].tolist() == ["B"]


def test_csv_provider_missing_file_explains_where_to_get_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="kaggle"):
        CSVDataProvider(tmp_path / "missing.csv")

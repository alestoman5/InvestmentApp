"""Tests for StatsCalculator.calculate."""

from __future__ import annotations

import pandas as pd
import pytest

from strategies.stats_calculator import StatsCalculator


def _series(values, start="2020-01-01", freq="D"):
    idx = pd.date_range(start, periods=len(values), freq=freq)
    return pd.Series(values, index=idx, dtype=float)


def test_none_and_empty_return_none():
    assert StatsCalculator.calculate(None) is None
    assert StatsCalculator.calculate(pd.Series(dtype=float)) is None


def test_total_return():
    stats = StatsCalculator.calculate(_series([100, 110, 150]))
    assert stats.total_return == pytest.approx(50.0)


def test_annualized_return_matches_total_over_one_year():
    # Exactly 365.25 days cannot be hit with daily stamps, so check the formula.
    s = pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-01-01", "2022-01-01"]))
    stats = StatsCalculator.calculate(s)
    years = 731 / 365.25
    expected = (2.0 ** (1 / years) - 1) * 100
    assert stats.annualized_return == pytest.approx(round(expected, 2))


def test_max_drawdown():
    stats = StatsCalculator.calculate(_series([1.0, 2.0, 1.0, 1.5]))
    assert stats.max_drawdown == pytest.approx(-50.0)


def test_flat_series_has_zero_volatility_and_sharpe():
    stats = StatsCalculator.calculate(_series([1.0] * 30))
    assert stats.volatility == 0
    assert stats.sharpe_ratio == 0
    assert stats.max_drawdown == 0


def test_monthly_win_rate():
    # Month-end values: Jan 1.0, Feb 1.1 (up), Mar 1.0 (down), Apr 1.2 (up).
    s = pd.Series(
        [1.0, 1.1, 1.0, 1.2],
        index=pd.to_datetime(["2021-01-31", "2021-02-28", "2021-03-31", "2021-04-30"]),
    )
    stats = StatsCalculator.calculate(s)
    assert stats.win_rate == pytest.approx(66.67, abs=0.01)


def test_single_point_does_not_crash():
    stats = StatsCalculator.calculate(_series([1.0]))
    assert stats.total_return == 0
    assert stats.annualized_return == 0

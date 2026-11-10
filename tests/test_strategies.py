"""Tests for the built-in strategies and the registry (no network access)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategies import REG, BuyAndHoldStrategy, PeriodicRebalanceStrategy

IDX = pd.date_range("2020-01-01", periods=3, freq="D")


def test_registry_contains_builtin_strategies():
    assert REG["Buy and Hold"] is BuyAndHoldStrategy
    assert REG["Periodic Rebalance"] is PeriodicRebalanceStrategy


def test_buy_and_hold_equal_weight(fake_prices):
    # A doubles then falls back; B is flat.
    fake_prices(pd.DataFrame({"A": [10, 20, 10], "B": [10, 10, 10]}, index=IDX))
    s = BuyAndHoldStrategy(["A", "B"], "2020-01-01", "2020-01-03").portfolio_series
    assert s.tolist() == pytest.approx([1.0, 1.5, 1.0])


def test_rebalance_differs_from_buy_and_hold(fake_prices):
    # Daily rebalancing: +50% on day 2, then (-50% + 0%) / 2 = -25% on day 3.
    fake_prices(pd.DataFrame({"A": [10, 20, 10], "B": [10, 10, 10]}, index=IDX))
    s = PeriodicRebalanceStrategy(["A", "B"], "2020-01-01", "2020-01-03").portfolio_series
    assert s.tolist() == pytest.approx([1.0, 1.5, 1.125])


def test_buy_and_hold_drops_ticker_without_first_price(fake_prices):
    fake_prices(pd.DataFrame({"A": [10, 11, 12], "B": [np.nan, 5, 50]}, index=IDX))
    s = BuyAndHoldStrategy(["A", "B"], "2020-01-01", "2020-01-03").portfolio_series
    assert s.tolist() == pytest.approx([1.0, 1.1, 1.2])


def test_tickers_missing_from_price_data_are_ignored(fake_prices):
    fake_prices(pd.DataFrame({"A": [10, 20, 30]}, index=IDX))
    s = BuyAndHoldStrategy(["A", "DELISTED"], "2020-01-01", "2020-01-03").portfolio_series
    assert s.tolist() == pytest.approx([1.0, 2.0, 3.0])


@pytest.mark.parametrize("cls", [BuyAndHoldStrategy, PeriodicRebalanceStrategy])
def test_no_price_data_gives_empty_series(fake_prices, cls):
    fake_prices(pd.DataFrame())
    strat = cls(["A"], "2020-01-01", "2020-01-03")
    assert strat.portfolio_series.empty
    assert strat.get_statistics() is None


def test_plot_returns_figure(fake_prices):
    fake_prices(pd.DataFrame({"A": [10, 20, 30]}, index=IDX))
    fig = BuyAndHoldStrategy(["A"], "2020-01-01", "2020-01-03").plot()
    assert fig.axes and fig.axes[0].get_title() == "Portfolio Performance"

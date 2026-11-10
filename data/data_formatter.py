"""Format raw data into Close price series."""

from __future__ import annotations
from typing import Sequence, Dict

import pandas as pd


class DataFormatter:
    """Convert raw yfinance output to ticker-close Series mapping."""

    @staticmethod
    def format_data(
        raw: pd.DataFrame, tickers: Sequence[str]
    ) -> Dict[str, pd.Series]:
        """Return dict of closing price Series for each ticker.

        Recent yfinance versions return (ticker, field) MultiIndex columns even
        for a single ticker (``multi_level_index=True`` by default); older ones
        return flat ``Open/High/.../Close`` columns. Both shapes are handled so a
        lone ticker is not silently dropped.
        """
        formatted: Dict[str, pd.Series] = {}
        if raw is None or raw.empty:
            return formatted

        multi = isinstance(raw.columns, pd.MultiIndex)
        for ticker in tickers:
            try:
                if multi:
                    series = raw[ticker]["Close"]
                elif len(tickers) == 1:
                    series = raw["Close"]
                else:
                    continue
            except (KeyError, TypeError):
                continue
            formatted[ticker] = series
        return formatted

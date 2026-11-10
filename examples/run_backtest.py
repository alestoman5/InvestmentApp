"""Headless backtest: run every registered strategy and save a chart + stats.

No Tkinter and no fundamentals CSV needed — you pass the tickers directly.

Real prices (needs internet, uses yfinance):
    python examples/run_backtest.py AAPL MSFT JNJ PG XOM --start 2015-01-01 --end 2023-06-30

Offline demo on synthetic prices (deterministic, seed 42):
    python examples/run_backtest.py --synthetic

Outputs go to examples/output/: equity_curve.png and results.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from strategies import REG  # noqa: E402  (path set above)
from strategies import strategy_abstract  # noqa: E402

STAT_LABELS = [
    ("total_return", "Total return (%)"),
    ("annualized_return", "Annualized return (%)"),
    ("volatility", "Volatility, ann. (%)"),
    ("max_drawdown", "Max drawdown (%)"),
    ("sharpe_ratio", "Sharpe ratio (rf = 2%)"),
    ("win_rate", "Monthly win rate (%)"),
]


def synthetic_prices(start: str, end: str, n: int = 5, seed: int = 42) -> pd.DataFrame:
    """Geometric Brownian motion paths with different drifts and volatilities."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, end)
    mu = np.linspace(0.02, 0.14, n) / 252
    sigma = np.linspace(0.15, 0.40, n) / np.sqrt(252)
    shocks = rng.normal(mu - 0.5 * sigma**2, sigma, size=(len(idx), n))
    paths = 100 * np.exp(np.cumsum(shocks, axis=0))
    return pd.DataFrame(paths, index=idx, columns=[f"SYN{i + 1}" for i in range(n)])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tickers", nargs="*", help="Ticker symbols (ignored with --synthetic)")
    p.add_argument("--start", default="2015-01-01")
    p.add_argument("--end", default="2023-06-30")
    p.add_argument("--synthetic", action="store_true", help="Use offline synthetic prices")
    p.add_argument("--out", type=Path, default=ROOT / "examples" / "output")
    args = p.parse_args()

    if args.synthetic:
        prices = synthetic_prices(args.start, args.end)
        tickers = list(prices.columns)
        strategy_abstract.DataFetcher.fetch_data = staticmethod(lambda *_: prices)
        source = "synthetic GBM prices (seed 42) — illustrative only, not market data"
    else:
        if not args.tickers:
            p.error("give tickers, or use --synthetic")
        tickers = args.tickers
        source = "Yahoo Finance daily closes via yfinance"

    results = {name: cls(tickers, args.start, args.end) for name, cls in REG.items()}
    results = {n: s for n, s in results.items() if s.portfolio_series is not None and not s.portfolio_series.empty}
    if not results:
        sys.exit("No price data returned — check tickers, dates and your connection.")

    args.out.mkdir(parents=True, exist_ok=True)

    fig = Figure(figsize=(10, 5.5))
    ax = fig.add_subplot(111)
    for name, strat in results.items():
        ax.plot(strat.portfolio_series, label=name, linewidth=1.4)
    ax.set_title(f"Equal-weight portfolio of {len(tickers)} stocks, {args.start} – {args.end}")
    ax.set_ylabel("Normalized value (start = 1)")
    ax.grid(linestyle="--", linewidth=0.5)
    ax.legend()
    fig.text(0.01, 0.01, f"Data: {source}", fontsize=8, color="grey")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    png = args.out / "equity_curve.png"
    fig.savefig(png, dpi=120)

    stats = {n: s.get_statistics() for n, s in results.items()}
    lines = [
        "# Sample backtest result",
        "",
        f"- **Tickers:** {', '.join(tickers)}",
        f"- **Period:** {args.start} – {args.end}",
        f"- **Data:** {source}",
        "",
        "| Metric | " + " | ".join(stats) + " |",
        "| --- | " + " | ".join("---:" for _ in stats) + " |",
    ]
    for key, label in STAT_LABELS:
        lines.append(f"| {label} | " + " | ".join(f"{getattr(s, key):.2f}" for s in stats.values()) + " |")
    lines += ["", "![Equity curve](equity_curve.png)", ""]
    md = args.out / "results.md"
    md.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines[6:-2]))
    print(f"\nSaved {png} and {md}")


if __name__ == "__main__":
    main()

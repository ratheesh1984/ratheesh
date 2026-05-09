"""
Screener orchestration: fetch -> compute -> filter -> rank.
"""
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd

from .fetcher import extract_close_volume, fetch_ohlcv_batch, fetch_pe_batch
from .indicators import average_volume, compute_rsi, compute_volume_ratio

log = logging.getLogger(__name__)

# Filter thresholds
PE_MIN = 0.0
PE_MAX = 20.0
VOLUME_RATIO_MIN = 1.5
RSI_MIN = 20.0
RSI_PERIOD = 14
VOLUME_LOOKBACK = 20
MIN_AVG_VOLUME = 50_000  # filter out illiquid names


@dataclass
class ScreenResult:
    ticker: str
    price: float
    pe: float
    volume_ratio: float
    rsi: float
    avg_volume: float
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def _composite_score(volume_ratio: float, rsi: float, pe: float) -> float:
    """
    Composite ranking score:
        volume_ratio * (rsi/50) * (20/pe)

    Rewards higher volume spikes, stronger momentum, cheaper valuation.
    All three factors are >= 1.0 at the filter thresholds, so the score
    grows multiplicatively as a stock exceeds them.
    """
    if pe <= 0 or volume_ratio <= 0 or rsi <= 0:
        return 0.0
    return volume_ratio * (rsi / 50.0) * (20.0 / pe)


def run_screen(
    universe: list[str],
    progress_cb: Optional[callable] = None,
) -> list[ScreenResult]:
    """
    Execute the full screening pipeline on the given ticker universe.

    Pipeline:
      1. Batched OHLCV download (one HTTP call).
      2. For each ticker: compute current price, volume_ratio, rsi.
      3. First-pass filter on volume_ratio > 2.0 AND rsi > 50.
      4. Fetch P/E only for first-pass survivors.
      5. Apply 0 < pe < 20 and rank by composite score.

    Args:
        universe: list of yfinance tickers (NSE symbols use ".NS" suffix)
        progress_cb: optional callable(stage: str, pct: float) for UI updates

    Returns:
        List of ScreenResult, sorted by score descending.
    """
    if not universe:
        return []

    def progress(stage: str, pct: float):
        if progress_cb:
            try:
                progress_cb(stage, pct)
            except Exception:
                pass

    # --- 1. Batched OHLCV ---
    progress("Fetching price & volume history…", 0.10)
    ohlcv = fetch_ohlcv_batch(universe, period="60d", interval="1d")
    if ohlcv.empty:
        log.error("No OHLCV data returned for universe of %d tickers", len(universe))
        return []

    # --- 2. Compute indicators per ticker ---
    progress("Computing RSI & volume ratios…", 0.40)
    survivors: list[dict] = []
    for ticker in universe:
        close, volume = extract_close_volume(ohlcv, ticker)
        if close.empty or volume.empty or len(close) < RSI_PERIOD + 1:
            continue

        avg_vol = average_volume(volume, lookback=VOLUME_LOOKBACK)
        if pd.isna(avg_vol) or avg_vol < MIN_AVG_VOLUME:
            continue

        vol_ratio = compute_volume_ratio(volume, lookback=VOLUME_LOOKBACK)
        rsi = compute_rsi(close, period=RSI_PERIOD)

        if pd.isna(vol_ratio) or pd.isna(rsi):
            continue

        # First-pass filter (cheap signals only)
        if vol_ratio <= VOLUME_RATIO_MIN or rsi <= RSI_MIN:
            continue

        survivors.append({
            "ticker": ticker,
            "price": float(close.iloc[-1]),
            "volume_ratio": vol_ratio,
            "rsi": rsi,
            "avg_volume": avg_vol,
        })

    if not survivors:
        progress("No tickers passed volume/RSI filter", 1.0)
        return []

    # --- 3. P/E fetch only for survivors (expensive per-call) ---
    progress(f"Fetching P/E for {len(survivors)} candidates…", 0.70)
    survivor_tickers = [s["ticker"] for s in survivors]
    pe_map = fetch_pe_batch(survivor_tickers)

    # --- 4. Apply P/E filter & build results ---
    progress("Ranking results…", 0.95)
    results: list[ScreenResult] = []
    for s in survivors:
        pe = pe_map.get(s["ticker"], float("nan"))
        if pd.isna(pe) or pe <= PE_MIN or pe >= PE_MAX:
            continue
        score = _composite_score(s["volume_ratio"], s["rsi"], pe)
        results.append(ScreenResult(
            ticker=s["ticker"],
            price=s["price"],
            pe=pe,
            volume_ratio=s["volume_ratio"],
            rsi=s["rsi"],
            avg_volume=s["avg_volume"],
            score=score,
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    progress("Done", 1.0)
    return results

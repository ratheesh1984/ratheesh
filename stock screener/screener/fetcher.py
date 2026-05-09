"""
yfinance data fetcher with rate-limiting and retry logic.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def fetch_ohlcv_batch(
    tickers: list[str],
    period: str = "30d",
    interval: str = "1d",
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Batched download of OHLCV for many tickers in a single HTTP call.

    Returns a multi-column DataFrame with columns like ('Close', 'AAPL'),
    ('Volume', 'AAPL'), etc. Empty/failed tickers are dropped silently.

    Uses exponential backoff on failure.
    """
    if not tickers:
        return pd.DataFrame()

    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            df = yf.download(
                tickers=tickers,
                period=period,
                interval=interval,
                group_by="column",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if df is None or df.empty:
                raise RuntimeError("Empty dataframe returned")
            return df
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            log.warning(
                "Batch fetch attempt %d/%d failed: %s. Retrying in %ds",
                attempt + 1, max_retries, e, wait,
            )
            time.sleep(wait)

    log.error("All batch fetch attempts failed: %s", last_err)
    return pd.DataFrame()


def fetch_pe_single(ticker: str, max_retries: int = 2) -> float:
    """
    Fetch trailing P/E for one ticker. Returns NaN if unavailable.
    """
    for attempt in range(max_retries):
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            pe = info.get("trailingPE")
            if pe is None:
                # Some tickers expose forwardPE only
                pe = info.get("forwardPE")
            if pe is None:
                return float("nan")
            return float(pe)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                log.debug("P/E fetch failed for %s: %s", ticker, e)
                return float("nan")
    return float("nan")


def fetch_pe_batch(
    tickers: list[str],
    max_workers: int = 5,
    inter_call_sleep: float = 0.1,
) -> dict[str, float]:
    """
    Concurrent P/E fetch for a small list of tickers.

    Limited to `max_workers` parallel requests to be polite to Yahoo's
    endpoints. Only call this on the post-filter survivor list (typically
    <20 tickers), not on the full universe.
    """
    if not tickers:
        return {}

    results: dict[str, float] = {}

    def _job(t: str) -> tuple[str, float]:
        time.sleep(inter_call_sleep)  # gentle pacing
        return t, fetch_pe_single(t)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_job, t): t for t in tickers}
        for fut in as_completed(futures):
            try:
                ticker, pe = fut.result()
                results[ticker] = pe
            except Exception as e:
                log.debug("P/E job error: %s", e)
                results[futures[fut]] = float("nan")

    return results


def extract_close_volume(
    df: pd.DataFrame, ticker: str
) -> tuple[pd.Series, pd.Series]:
    """
    Pull (close, volume) series for one ticker out of a batched download.

    Handles both the multi-ticker MultiIndex layout and the single-ticker
    flat layout that yf.download returns.
    """
    if df.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    # Multi-ticker download: columns are (field, ticker)
    if isinstance(df.columns, pd.MultiIndex):
        try:
            close = df["Close"][ticker].dropna()
            volume = df["Volume"][ticker].dropna()
            return close, volume
        except KeyError:
            return pd.Series(dtype=float), pd.Series(dtype=float)

    # Single-ticker download: flat columns
    try:
        return df["Close"].dropna(), df["Volume"].dropna()
    except KeyError:
        return pd.Series(dtype=float), pd.Series(dtype=float)

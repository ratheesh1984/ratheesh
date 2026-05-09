"""
Technical indicators.
"""
import numpy as np
import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> float:
    """
    Wilder's RSI on a price series. Returns the most recent RSI value.

    Wilder's smoothing uses an exponential moving average with alpha = 1/period
    (equivalent to a smoothed moving average), which is the standard RSI
    formulation used by virtually all charting platforms.

    Returns NaN if the series has fewer than `period + 1` valid points.
    """
    close = close.dropna()
    if len(close) < period + 1:
        return float("nan")

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: alpha = 1/period, equivalent to EMA with com=period-1
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    last = rsi.iloc[-1]
    if pd.isna(last) or np.isinf(last):
        return float("nan")
    return float(last)


def compute_volume_ratio(volume: pd.Series, lookback: int = 20) -> float:
    """
    Today's volume divided by the mean of the previous `lookback` days
    (excluding today). Returns NaN on insufficient data or zero average.
    """
    volume = volume.dropna()
    if len(volume) < lookback + 1:
        return float("nan")

    today = volume.iloc[-1]
    prior_avg = volume.iloc[-(lookback + 1):-1].mean()
    if prior_avg <= 0 or pd.isna(prior_avg):
        return float("nan")
    return float(today / prior_avg)


def average_volume(volume: pd.Series, lookback: int = 20) -> float:
    """Mean of the previous `lookback` days, excluding today."""
    volume = volume.dropna()
    if len(volume) < lookback + 1:
        return float("nan")
    return float(volume.iloc[-(lookback + 1):-1].mean())

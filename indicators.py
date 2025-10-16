import pandas as pd
import numpy as np

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    h_l = (high - low).abs()
    h_pc = (high - close.shift()).abs()
    l_pc = (low - close.shift()).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    tp = (high + low + close) / 3.0
    cum_vol = volume.cumsum().replace(0, np.nan)
    cum_tp_vol = (tp * volume).cumsum()
    return cum_tp_vol / cum_vol

def volatility_band(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window).std() * np.sqrt(365*24*12)  # annualized approx

def liquidity_sweep(high: pd.Series, low: pd.Series, close: pd.Series, lookback:int=3):
    """Detects wicks that take out prior highs/lows and close back inside.
    Returns two boolean Series: sweep_high, sweep_low
    sweep_high: current high > max(prior highs N) and close < prior max high -> potential bearish sweep
    sweep_low:  current low  < min(prior lows N)  and close > prior min low  -> potential bullish sweep
    """
    prior_high = high.shift(1).rolling(lookback).max()
    prior_low  = low.shift(1).rolling(lookback).min()
    sweep_high = (high > prior_high) & (close < prior_high)
    sweep_low  = (low  < prior_low ) & (close > prior_low )
    return sweep_high.fillna(False), sweep_low.fillna(False)


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, reset_index: pd.Series | None = None) -> pd.Series:
    """Session/daily VWAP. If reset_index is provided (bool), resets cumulative sums when True."""
    typical = (high + low + close) / 3.0
    if reset_index is None:
        cum_price_vol = (typical * volume).cumsum()
        cum_vol = volume.cumsum() + 1e-9
        return cum_price_vol / cum_vol
    else:
        # Reset-aware cumulative
        cum_pv = pd.Series(index=typical.index, dtype=float)
        cum_v = pd.Series(index=typical.index, dtype=float)
        pv = 0.0; v = 0.0
        last_reset = None
        for idx in typical.index:
            if reset_index.loc[idx]:
                pv = 0.0; v = 0.0
            pv += typical.loc[idx] * volume.loc[idx]
            v += volume.loc[idx]
            cum_pv.loc[idx] = pv
            cum_v.loc[idx] = v + 1e-9
        return cum_pv / cum_v

def detect_sweep(high: pd.Series, low: pd.Series, close: pd.Series, lookback: int = 20):
    """Returns two boolean Series: high_sweep, low_sweep.
    High sweep: current high > rolling max of previous N highs, and close < prior max.
    Low sweep: current low < rolling min of previous N lows, and close > prior min.
    """
    prev_max = high.shift(1).rolling(lookback).max()
    prev_min = low.shift(1).rolling(lookback).min()
    high_sweep = (high > prev_max) & (close < prev_max)
    low_sweep = (low < prev_min) & (close > prev_min)
    return high_sweep.fillna(False), low_sweep.fillna(False)


def vwap_deviation_bands(close: pd.Series, vwap_series: pd.Series, window: int = 50):
    """Return (plus1, minus1, plus2, minus2) bands based on std of (close - vwap)."""
    delta = close - vwap_series
    sigma = delta.rolling(window).std()
    plus1 = vwap_series + sigma
    minus1 = vwap_series - sigma
    plus2 = vwap_series + 2*sigma
    minus2 = vwap_series - 2*sigma
    return plus1, minus1, plus2, minus2

import asyncio, ccxt, pandas as pd
from datetime import datetime, timezone
from .config import settings
from .indicators import rsi, ema, vwap, detect_sweep, vwap_deviation_bands
from .alert_router import AlertRouter

def _reset_index_for_vwap(index: pd.DatetimeIndex, mode: str = "DAILY"):
    if mode.upper() == "NONE":
        return pd.Series(False, index=index)
    if mode.upper() == "DAILY":
        # Reset when the date changes (UTC)
        days = index.tz_convert("UTC").date if index.tz is not None else index.tz_localize("UTC").date
        reset = pd.Series(False, index=index)
        prev = None
        for i, d in enumerate(days):
            if prev is None or d != prev:
                reset.iloc[i] = True
                prev = d
        return reset
    # SESSION: placeholder, could reset at session starts
    return pd.Series(False, index=index)

async def poll_symbol(exchange: ccxt.Exchange, symbol: str, router: AlertRouter):
    while True:
        try:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1m", limit=200)
            df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
            df.set_index("ts", inplace=True)

            if len(df) < 50:
                await asyncio.sleep(settings.mexc_poll_interval_sec)
                continue

            rs = rsi(df["close"], settings.rsi_period).iloc[-1]
            ema20 = ema(df["close"], 20).iloc[-1]

            reset_idx = _reset_index_for_vwap(df.index, settings.vwap_reset)
            v = vwap(df["high"], df["low"], df["close"], df["volume"], reset_idx).iloc[-1]

            hs, ls = detect_sweep(df["high"], df["low"], df["close"], settings.sweep_lookback)
            high_sweep = bool(hs.iloc[-1])
            low_sweep = bool(ls.iloc[-1])

            note = []
            if df["close"].iloc[-1] > ema20: note.append("close > EMA20")
            else: note.append("close < EMA20")
            if df["close"].iloc[-1] > v: note.append("above VWAP")
            else: note.append("below VWAP")
            if rs <= settings.rsi_oversold: note.append(f"RSI {rs:.1f} <= {settings.rsi_oversold}")
            if rs >= settings.rsi_overbought: note.append(f"RSI {rs:.1f} >= {settings.rsi_overbought}")
            if high_sweep: note.append("High Sweep")
            # VWAP bands
            p1, m1, p2, m2 = vwap_deviation_bands(df['close'], v, window=settings.vwap_band_window if hasattr(settings, 'vwap_band_window') else 50)
            if settings.enable_vwap_band_alerts:
                if df['close'].iloc[-1] >= p2.iloc[-1]: note.append('≥ +2σ above VWAP')
                elif df['close'].iloc[-1] >= p1.iloc[-1]: note.append('≥ +1σ above VWAP')
                if df['close'].iloc[-1] <= m2.iloc[-1]: note.append('≤ -2σ below VWAP')
                elif df['close'].iloc[-1] <= m1.iloc[-1]: note.append('≤ -1σ below VWAP')

            if low_sweep: note.append("Low Sweep")

            body = f"{symbol} close={df['close'].iloc[-1]:.2f} | " + ", ".join(note)
            await router.send("MEXC Scan", body, key=f"mexc-{symbol.replace('/', '')}")
        except Exception as e:
            print("MEXC poll error:", e)
        await asyncio.sleep(settings.mexc_poll_interval_sec)

async def run_mexc(router: AlertRouter):
    if not settings.enable_mexc:
        return
    ex = ccxt.mexc({'enableRateLimit': True})
    if settings.binance_key and settings.binance_secret:
        pass  # not used here
    tasks = []
    for sym in settings.mexc_symbols:
        tasks.append(asyncio.create_task(poll_symbol(ex, sym, router)))
    await asyncio.gather(*tasks)

import asyncio
import pandas as pd
from datetime import datetime, timezone

from binance import AsyncClient, BinanceSocketManager

from indicators import rsi, ema, vwap, liquidity_sweep  # keep only what you use
from config import settings
from alert_router import AlertRouter


class WSRunner:
    def _init_(self, router: AlertRouter):
        self.router = router

    async def run(self):
        if not settings.use_binance_ws:
            return

        # build streams once (e.g., "btcusdt@kline_1m")
        streams: list[str] = []
        for s in [c.strip().upper() for c in settings.coins]:
            streams.append(f"{s}{settings.base}@kline_1m".lower())

        cache: dict[str, pd.DataFrame] = {}

        # reconnect loop
        while True:
            client: AsyncClient | None = None
            try:
                client = await AsyncClient.create()
                bsm = BinanceSocketManager(client)
                ms = bsm.multiplex_socket(streams)

                async for msg in ms:
                    data = msg.get("data", {})
                    k = data.get("k", {})
                    if not k:
                        continue

                    symbol = k.get("s")              # BTCUSDT
                    is_closed = k.get("x")           # candle closed?
                    o = float(k.get("o", 0))
                    h = float(k.get("h", 0))
                    l = float(k.get("l", 0))
                    c = float(k.get("c", 0))
                    v = float(k.get("v", 0))
                    ts = datetime.fromtimestamp(k.get("t", 0) / 1000, tz=timezone.utc)

                    df = cache.get(symbol)
                    if df is None:
                        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
                    df.loc[ts] = {"open": o, "high": h, "low": l, "close": c, "volume": v}
                    if len(df) > 500:
                        df = df.iloc[-500:]
                    cache[symbol] = df

                    if is_closed and len(df) > 30:
                        close = df["close"]
                        high = df["high"]
                        low = df["low"]
                        vol = df["volume"]

                        rs_val = rsi(close, settings.rsi_period).iloc[-1]
                        ema20 = ema(close, 20).iloc[-1]
                        vwap_now = vwap(high, low, close, vol).iloc[-1]
                        sh, sl = liquidity_sweep(high, low, close, vol, lookback=5)
                        swept_hi = bool(sh.iloc[-1])
                        swept_lo = bool(sl.iloc[-1])

                        notes: list[str] = []
                        notes.append(f"close={close.iloc[-1]:.2f}")
                        notes.append(f"RSI={rs_val:.1f}")
                        notes.append(f"EMA20={'above' if close.iloc[-1] > ema20 else 'below'}")
                        notes.append(f"VWAP={'above' if close.iloc[-1] > vwap_now else 'below'}")
                        if swept_hi:
                            notes.append("Liquidity sweep of prior HIGH → potential fade")
                        if swept_lo:
                            notes.append("Liquidity sweep of prior LOW → potential long")

                        if swept_hi or swept_lo or abs(close.iloc[-1] - ema20) / max(ema20, 1e-9) > 0.001:
                            body = f"{symbol} | " + ", ".join(notes)
                            key = f"{symbol}-sweep" if (swept_hi or swept_lo) else f"{symbol}-indicators"
                            await self.router.send("Binance 1m Signal", body, key=key)

            except Exception as e:
                print(f"⚠ WebSocket error: {e}. Reconnecting in 5s…")
                await asyncio.sleep(5)
            finally:
                if client is not None:
                    try:
                        await client.close_connection()
                    except Exception:
                        pass

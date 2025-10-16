import asyncio, pandas as pd
from datetime import datetime, timezone
from binance import AsyncClient, BinanceSocketManager
from indicators import rsi, ema, vwap, vwap_deviation_bands, vwap, liquidity_sweep
from config import settings
from alert_router import AlertRouter

class WSRunner:
    def __init__(self, router: AlertRouter):
        self.router = router

    async def run(self):
        if not settings.use_binance_ws:
            return
        client = await AsyncClient.create()
        bsm = BinanceSocketManager(client)
        streams = []
        for c in [s.strip().upper() for s in settings.coins]:
            streams.append(f"{c}{settings.base}@kline_1m".lower())
        ms = bsm.multiplex_socket(streams)
        async for msg in ms:
                data = msg.get('data', {})
                k = data.get('k', {})
                if not k:
                    continue
                symbol = k.get('s')  # e.g., BTCUSDT
                is_closed = k.get('x')
                o = float(k.get('o')); h = float(k.get('h')); l = float(k.get('l'))
                c = float(k.get('c')); v = float(k.get('v'))
                ts = datetime.fromtimestamp(k.get('t')/1000, tz=timezone.utc)

                df = cache.get(symbol)
                if df is None:
                    df = pd.DataFrame(columns=['open','high','low','close','volume'])
                df.loc[ts] = {'open':o,'high':h,'low':l,'close':c,'volume':v}
                if len(df) > 500:
                    df = df.iloc[-500:]
                cache[symbol] = df

                if is_closed and len(df) > 30:
                    close = df['close']
                    high = df['high']; low=df['low']; vol=df['volume']

                    rs = rsi(close, settings.rsi_period).iloc[-1]
                    ema20 = ema(close, 20).iloc[-1]
                    vwap_now = vwap(high, low, close, vol).iloc[-1]
                    sh, sl = liquidity_sweep(high, low, close, lookback=5)
                    swept_hi = bool(sh.iloc[-1])
                    swept_lo = bool(sl.iloc[-1])

                    notes = []
                    notes.append(f"close={close.iloc[-1]:.2f}")
                    notes.append(f"RSI={rs:.1f}")
                    notes.append(f"EMA20={'above' if close.iloc[-1]>ema20 else 'below'}")
                    notes.append(f"VWAP={'above' if close.iloc[-1]>vwap_now else 'below'}")
                    if swept_hi: notes.append("Liquidity sweep of prior HIGH → potential fade")
                    if swept_lo: notes.append("Liquidity sweep of prior LOW → potential long" )

                    if swept_hi or swept_lo or abs(close.iloc[-1]-ema20)/ema20>0.001:
                        body = f"{symbol} | " + ", ".join(notes)
                        key = f"{symbol}-sweep" if (swept_hi or swept_lo) else f"{symbol}-indicators"
                        await self.router.send("Binance 1m Signal", body, key=key)

        await client.close_connection()

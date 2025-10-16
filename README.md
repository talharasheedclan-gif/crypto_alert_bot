# Crypto Alert & News Bot (Advanced)

A production‑ready Telegram bot + webhook service for **crypto alerts, news, whale moves, and TradingView signals**. 
Designed for VPS/Docker deployment.

## Key features
- **Telegram alerts**: price/volatility spikes, RSI/MAs crosses, whale transfers, gas spikes, and custom TradingView signals.
- **Data sources**: Binance websockets (via `python-binance`), exchange REST (via `ccxt`), NewsAPI/CryptoNews API, optional on-chain (Etherscan).
- **TradingView webhook endpoint**: accept JSON alerts from your Pine script; routes to Telegram and optional auto‑trade endpoints.
- **Smart throttling & de-duplication**: avoid spamming repeats; configurable cooldowns.
- **Rules engine**: YAML/ENV-driven rules for coins, time windows (Dubai/London/NY sessions), and thresholds.
- **Risk controls**: guardrails on auto-trade webhooks (max size, per‑day cap, circuit breaker). Disabled by default.
- **Modular**: separate modules for indicators, news, whale watch, and websocket feed.
- **Dockerized**: deploy in minutes; supports `.env` config.

## Quick start (Docker)
1. Copy `.env.example` to `.env` and fill your keys (Telegram, NewsAPI, Etherscan optional).
2. Run:
```bash
docker compose up -d --build
```
3. In TradingView, paste the **Pine** script from `tradingview/advanced_signals.pine`, add alerts with the provided JSON in `tradingview/webhook_examples.json`, and set the webhook URL to:
```
https://<your-server-domain-or-ip>/tvhook
```
4. You’ll start receiving alerts in Telegram.

## Local run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## Files
- `src/main.py` — FastAPI app with `/health`, `/tvhook` (TradingView), `/test`, scheduled jobs.
- `src/exchange_ws.py` — Binance websocket listeners for ticker/klines, with alert checks.
- `src/indicators.py` — TA helpers (RSI, EMA/MA, ATR, volatility bands).
- `src/news.py` — pulls + filters crypto news, throttles duplicates, keyword whitelist/blacklist.
- `src/whale_watch.py` — sample on-chain watchers (Etherscan API), exchange inflow/outflow heuristics.
- `src/alert_router.py` — routes events to Telegram, with cooldowns + formatting.
- `tradingview/advanced_signals.pine` — Pine v5 strategy/indicator to emit JSON alerts.
- `tradingview/webhook_examples.json` — ready-made alert payload templates.

## Security & Safety
- Keep your bot token/keys in `.env`.
- If enabling auto‑trade webhooks, start in **paper mode** and set small max notional caps.
- Never store private keys here. Use exchange sub‑accounts and IP allowlists.

## Timezones
- Defaults to **Asia/Dubai**; session windows for **London** and **New York** are configurable via ENV.

— Generated 2025-10-15T22:04:53.470771Z


---
## v2 Upgrade — MEXC + VWAP + Liquidity Sweeps  (2025-10-15T22:13:28.450686Z)

### What’s new
- **MEXC integration (ccxt)**: optional 1m polling for BTC/ETH (or your list) with the same indicator checks.
- **VWAP**: session‑aware VWAP calculation (reset daily by default).
- **Liquidity Sweep detector**: detects “sweep of highs/lows” (taking out prior swing then closing back inside).
- **TradingView Pine updated**: adds VWAP, sweep detection labels, and webhook JSON snippets.

### How to enable MEXC
Edit `.env`:
```
ENABLE_MEXC=true
MEXC_SYMBOLS=BTC/USDT,ETH/USDT
MEXC_POLL_INTERVAL_SEC=30
```
*(You can still keep Binance websockets on; both can run together.)*

### VWAP & Sweeps
- VWAP resets **daily**. Set `VWAP_RESET=DAILY` (alternatives: `SESSION`, `NONE`).
- Sweeps: use `SWEEP_LOOKBACK=20` (candles). A **high sweep** occurs when the candle’s high exceeds the highest high in the lookback but **closes back below** that prior high. Low sweep is the inverse.
- Alerts are tagged as `VWAP`, `High Sweep`, `Low Sweep`.



---
## v3 — 24/7 Mode Defaults  (2025-10-15T22:16:30.047053Z)

- Session filter **OFF by default** so alerts/news run all day.
- Scheduler runs every **5 minutes** (news) instead of 15 (configurable).
- Docker **healthcheck** added; container auto-restarts if unhealthy.
- Add tip for **server watchdog** and **log rotation**.



---
## v4 — VWAP ±Bands + 2‑Hour Heartbeat  (2025-10-15T22:20:51.890471Z)

### New
- **VWAP deviation bands** (±1σ / ±2σ) alerts for overbought/oversold extremes.
- **Heartbeat**: Telegram keep‑alive message every N seconds (default 2 hours).

### Configure
```
HEARTBEAT_SECONDS=7200
ENABLE_VWAP_BAND_ALERTS=true
VWAP_BAND_WINDOW=50
```

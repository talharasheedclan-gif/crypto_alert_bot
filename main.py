# main.py — production-safe entrypoint

import os
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from config import settings
from alert_router import AlertRouter
from exchange_ws import WSRunner
from mexc_poll import run_mexc
import news  # must define: async def run_news_cycle(router)

# ------------------------------------------------------------
# FastAPI app + alert router
# ------------------------------------------------------------

app = FastAPI()

# If your AlertRouter takes (token, chat_id), keep as-is.
# If it takes no args, change to: router = AlertRouter()
router = AlertRouter(
    settings.telegram_bot_token,
    settings.telegram_chat_id,
)

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "Crypto bot is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test")
async def test():
    await router.send("Test", "Hello from the bot!", key="test")
    return {"ok": True}

@app.post("/tvhook")
async def tvhook(request: Request):
    """
    TradingView webhook example payload:
    {
      "title": "BTC Breakout",
      "message": "Long above 125k",
      "key": "tv-btc"
    }
    """
    data = await request.json()
    title = str(data.get("title", "TradingView Alert"))
    message = str(data.get("message", data))
    key = str(data.get("key", "tv-default"))
    await router.send(title, message, key=key)
    return {"ok": True}

# ------------------------------------------------------------
# Background tasks
# ------------------------------------------------------------

async def heartbeat():
    """Periodic ping so you know the bot is alive."""
    while True:
        try:
            await router.send("Heartbeat", "Crypto bot running — OK ✅", key="heartbeat")
        except Exception as e:
            print("Heartbeat error:", e)
        await asyncio.sleep(60)

def _parse_hhmm(s: str) -> time:
    h, m = [int(x) for x in s.split(":")]
    return time(h, m)

def _within_session(now_t: time, start: str, end: str) -> bool:
    s = _parse_hhmm(start)
    e = _parse_hhmm(end)
    return s <= now_t <= e

async def scheduler():
    """
    Runs your news/task cycle:
      - every settings.scheduler_news_seconds seconds (default 900 / 15m)
      - if settings.enable_session_filter is true, only inside London/NY windows
    """
    tz = ZoneInfo(settings.timezone)
    interval = int(getattr(settings, "scheduler_news_seconds", 900))
    use_sessions = bool(getattr(settings, "enable_session_filter", False))

    while True:
        try:
            if not use_sessions:
                await news.run_news_cycle(router)
            else:
                now_t = datetime.now(tz).time()
                in_london = _within_session(now_t, settings.london_start, settings.london_end)
                in_ny     = _within_session(now_t, settings.ny_start, settings.ny_end)
                if in_london or in_ny:
                    await news.run_news_cycle(router)
        except Exception as e:
            print("scheduler error:", e)

        await asyncio.sleep(interval)

# ------------------------------------------------------------
# Startup hook: launch runners
# ------------------------------------------------------------

@app.on_event("startup")
async def startup():
    # Binance WebSocket runner
    asyncio.create_task(WSRunner(router).run())

    # MEXC poller (guarded by ENABLE_MEXC)
    if bool(getattr(settings, "enable_mexc", True)):
        asyncio.create_task(run_mexc(router))

    # Support tasks
    asyncio.create_task(heartbeat())
    asyncio.create_task(scheduler())

# ------------------------------------------------------------
# Local run (when not using uvicorn CLI)
# ------------------------------------------------------------

if _name_ == "_main_":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=False,
    )

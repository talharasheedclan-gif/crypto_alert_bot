# main.py — drop-in, production-ready

import os
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request

from config import settings
from alert_router import AlertRouter
from exchange_ws import WSRunner
from mexc_poll import run_mexc            # must accept (router)
import news                                # must expose run_news_cycle(router)

# ----- FastAPI app & router ---------------------------------------------------

app = FastAPI()
router = AlertRouter(
    settings.telegram_bot_token,
    settings.telegram_chat_id,
)

# ----- Routes -----------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/tvhook")
async def tvhook(request: Request):
    payload = await request.json()
    title = str(payload.get("title", "TV Alert"))
    body = str(payload.get("message", payload))
    key = str(payload.get("key", "tv-default"))
    await router.send(title, body, key=key)
    return {"ok": True}

@app.get("/test")
async def test():
    await router.send("Test", "hello from the bot!", key="test")
    return {"ok": True}

# ----- Background tasks -------------------------------------------------------

async def heartbeat():
    """Send a tiny heartbeat to confirm the bot is alive."""
    while True:
        try:
            await router.send("Heartbeat", "Crypto bot running — OK", key="heartbeat")
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
    Run your news/task cycle on a fixed cadence, optionally respecting
    session windows (London / NY) if enable_session_filter is true.
    """
    tz = ZoneInfo(settings.timezone)
    interval = int(getattr(settings, "scheduler_news_seconds", 900))  # default 15m
    while True:
        try:
            now_t = datetime.now(tz).time()
            do_sessions = bool(getattr(settings, "enable_session_filter", False))

            if not do_sessions:
                await news.run_news_cycle(router)
            else:
                in_london = _within_session(now_t, settings.london_start, settings.london_end)
                in_ny     = _within_session(now_t, settings.ny_start, settings.ny_end)
                if in_london or in_ny:
                    await news.run_news_cycle(router)
        except Exception as e:
            print("scheduler error:", e)
        await asyncio.sleep(interval)

# ----- Startup hook -----------------------------------------------------------

@app.on_event("startup")
async def startup():
    # Binance WebSocket runner
    asyncio.create_task(WSRunner(router).run())

    # MEXC poller (only if enabled in settings)
    if bool(getattr(settings, "enable_mexc", True)):
        asyncio.create_task(run_mexc(router))

    # Support tasks
    asyncio.create_task(heartbeat())
    asyncio.create_task(scheduler())

# ----- Local run --------------------------------------------------------------

if _name_ == "_main_":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=False,
    )

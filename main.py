import asyncio, os
from fastapi import FastAPI, Request, Response
import uvicorn
from datetime import datetime, time
from zoneinfo import ZoneInfo
from config import settings
from alert_router import AlertRouter
from exchange_ws import WSRunner
from mexc_poll import run_mexc
import news


app = FastAPI()
router = AlertRouter(settings.telegram_bot_token, settings.telegram_chat_id, settings.duplicate_cooldown_seconds)

@app.get('/health')
async def health():
    return {"status": "ok"}

@app.post('/tvhook')
async def tvhook(request: Request):
    payload = await request.json()
    title = payload.get("title", "TV Alert")
    body = payload.get("message", str(payload))
    key = payload.get("key", "tv-default")
    await router.send(title, body, key=key)
    return {"ok": True}

@app.get('/test')
async def test():
    await router.send("Test", "Hello from the bot!", key="test")
    return {"ok": True}


async def heartbeat():
    while True:
        try:
            await router.send("Heartbeat", "Crypto bot running — feeds OK.", key="heartbeat")
        except Exception as e:
            print("Heartbeat error:", e)
        await asyncio.sleep(settings.heartbeat_seconds)


async def scheduler():
    tz = ZoneInfo(settings.timezone)
    while True:
        now = datetime.now(tz).time()
        # Example: run news every 15 minutes during sessions
        def within(start: str, end: str):
            s = time.fromisoformat(start); e = time.fromisoformat(end)
            return s <= now <= e
        if (not settings.enable_session_filter) or within(settings.london_start, settings.london_end) or within(settings.ny_start, settings.ny_end):
            news_mod.run_news_cycle(router)
        await asyncio.sleep(settings.scheduler_news_seconds)  # 15m

@app.on_event("startup")
async def startup():
    asyncio.create_task(WSRunner(router).run())
    asyncio.create_task(MEXCPoller(router).run())
    asyncio.create_task(scheduler())

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=False)

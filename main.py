import asyncio
import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from exchange_ws import ExchangeWS

# Structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("app")

app = FastAPI(title="Exchange WS Service", version="1.0.0")

# Global holder for the WS client & task
_ws_client: Optional[ExchangeWS] = None
_ws_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def on_startup():
    global _ws_client, _ws_task
    log.info("Starting up...")

    # Example: read settings from env (override as needed)
    ws_url = os.getenv("WS_URL", "wss://echo.websocket.events")  # replace with real exchange WS URL
    ping_interval = float(os.getenv("WS_PING_INTERVAL", "20"))
    reconnect_delay = float(os.getenv("WS_RECONNECT_DELAY", "5"))

    _ws_client = ExchangeWS(
        url=ws_url,
        ping_interval=ping_interval,
        reconnect_delay=reconnect_delay,
    )

    # Launch background task
    _ws_task = asyncio.create_task(_ws_client.run(), name="exchange-ws-runner")
    log.info("Background WS task started.")

@app.on_event("shutdown")
async def on_shutdown():
    global _ws_client, _ws_task
    log.info("Shutting down...")
    if _ws_client:
        await _ws_client.close()
    if _ws_task:
        _ws_task.cancel()
        try:
            await _ws_task
        except asyncio.CancelledError:
            pass
    log.info("Shutdown complete.")

@app.get("/health")
async def health():
    status = "up" if _ws_client and _ws_client.connected else "degraded"
    return JSONResponse({"status": status, "connected": bool(_ws_client and _ws_client.connected)})

@app.get("/")
async def root():
    return {"service": "Exchange WS Service", "version": "1.0.0"}

# main.py
import asyncio, logging, os
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from ws_client import ExchangeWS

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("app")

_ws_client: Optional[ExchangeWS] = None
_ws_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ws_client, _ws_task
    log.info("Starting up...")
    ws_url = os.getenv("WS_URL", "wss://echo.websocket.events")
    ping_interval = float(os.getenv("WS_PING_INTERVAL", "20"))
    reconnect_delay = float(os.getenv("WS_RECONNECT_DELAY", "5"))
    _ws_client = ExchangeWS(url=ws_url, ping_interval=ping_interval, reconnect_delay=reconnect_delay)
    _ws_task = asyncio.create_task(_ws_client.run(), name="exchange-ws-runner")
    yield
    log.info("Shutting down...")
    if _ws_client:
        await _ws_client.close()
    if _ws_task:
        _ws_task.cancel()
        try: await _ws_task
        except asyncio.CancelledError: pass

app = FastAPI(title="Exchange WS Service", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    ok = bool(_ws_client and _ws_client.connected)
    return JSONResponse({"status": "up" if ok else "degraded", "connected": ok})

@app.get("/")
async def root():
    return {"service": "Exchange WS Service", "version": "1.0.0"}

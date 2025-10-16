import asyncio
from fastapi import FastAPI
from alert_router import AlertRouter
from exchange_ws import WSRunner
from config import settings
from mexc_poll import run_mexc
from scheduler import scheduler, heartbeat

app = FastAPI()
router = AlertRouter()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(WSRunner(router).run())
    if getattr(settings, "enable_mexc", True):
        asyncio.create_task(run_mexc(router))
    asyncio.create_task(heartbeat())
    asyncio.create_task(scheduler())

if _name_ == "_main_":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

import asyncio, json, logging
from typing import Optional
import websockets

log = logging.getLogger("ws_client")

class WSClient:
    def _init_(self, url: str, ping_interval: float = 20.0, reconnect_delay: float = 5.0):
        self.url = url
        self.ping_interval = ping_interval
        self.reconnect_delay = reconnect_delay
        self._stop = asyncio.Event()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False

    async def run(self):
        while not self._stop.is_set():
            try:
                log.info(f"Connecting to {self.url} ...")
                async with websockets.connect(self.url, ping_interval=self.ping_interval) as ws:
                    self._ws = ws
                    self.connected = True
                    log.info("WebSocket connected.")
                    await self._on_open()
                    while not self._stop.is_set():
                        msg = await ws.recv()
                        await self._on_message(msg)
            except (OSError, websockets.WebSocketException) as e:
                self.connected = False
                log.warning(f"WS error: {e!r}. Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
            finally:
                self.connected = False
                self._ws = None

    async def _on_open(self):
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps({"type": "hello", "msg": "connected"}))
            log.info("Sent hello payload.")
        except Exception as e:
            log.error(f"Failed to send initial payload: {e!r}")

    async def _on_message(self, message: str):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {"raw": message}
        log.debug(f"Message: {data}")

    async def close(self):
        self._stop.set()
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

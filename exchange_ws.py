import asyncio
import json
import logging
from typing import Optional
import websockets

log = logging.getLogger("exchange_ws")

class ExchangeWS:
    def _init_(self, url: str, ping_interval: float = 20.0, reconnect_delay: float = 5.0):
        self.url = url
        self.ping_interval = ping_interval
        self.reconnect_delay = reconnect_delay
        self._stop = asyncio.Event()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected: bool = False

    async def run(self):
        """Main loop: connect, consume, and auto-reconnect on errors."""
        while not self._stop.is_set():
            try:
                log.info(f"Connecting to {self.url} ...")
                async with websockets.connect(self.url, ping_interval=self.ping_interval) as ws:
                    self._ws = ws
                    self.connected = True
                    log.info("WebSocket connected.")

                    await self._on_open()

                    consumer = asyncio.create_task(self._consume(), name="ws-consumer")
                    await self._stop.wait()
                    consumer.cancel()
                    try:
                        await consumer
                    except asyncio.CancelledError:
                        pass
            except (OSError, websockets.WebSocketException) as e:
                self.connected = False
                log.warning(f"WS error: {e!r}. Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
            finally:
                self.connected = False
                self._ws = None

    async def _consume(self):
        """Receive messages and dispatch."""
        assert self._ws is not None
        try:
            async for message in self._ws:
                await self._on_message(message)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error(f"Consumer crashed: {e!r}")

    async def _on_open(self):
        """Called after connect. Customize subscription here."""
        if self._ws is None:
            return
        hello = {"type": "hello", "msg": "connected"}
        try:
            await self._ws.send(json.dumps(hello))
            log.info("Sent hello payload.")
        except Exception as e:
            log.error(f"Failed to send initial payload: {e!r}")

    async def _on_message(self, message: str):
        """Handle incoming messages."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {"raw": message}
        log.debug(f"Message: {data}")

    async def close(self):
        """Request graceful shutdown."""
        self._stop.set()
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

import asyncio
import json
import logging
import threading
from typing import Callable, Optional

import websockets
from websockets.protocol import CLOSED

from .auth import AuthClient
from .ws_compat import LenientClientConnection

logger = logging.getLogger(__name__)

RECONNECT_DELAY = 5.0


class BaseWebSocketClient:
    def __init__(self, app_key: str, user_id: str, ws_url: str, auth: AuthClient | None = None):
        self.auth = auth or AuthClient(app_key, user_id)
        self.token = self.auth.get_token()
        self.ws_url = ws_url
        self.ws = None
        self.reconnect = True
        self._closing = False
        self.connected = False
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self.on_message_callback: Optional[Callable] = None
        self.on_connect_callback: Optional[Callable] = None
        self.on_close_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None

    def set_on_message(self, callback: Callable):
        self.on_message_callback = callback

    def set_on_connect(self, callback: Callable):
        self.on_connect_callback = callback

    def set_on_close(self, callback: Callable):
        self.on_close_callback = callback

    def set_on_error(self, callback: Callable):
        self.on_error_callback = callback

    def start(self):
        self.reconnect = True
        self._closing = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        try:
            self._loop.run_until_complete(self._run())
        except asyncio.CancelledError:
            pass
        finally:
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None

    async def _run(self):
        while self.reconnect and not self._closing:
            try:
                await self._connect_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("[WS] Error: %s", e)
                if self.on_error_callback:
                    self.on_error_callback(e)
            finally:
                self.connected = False
                self.ws = None
            if self.reconnect and not self._closing:
                await asyncio.sleep(RECONNECT_DELAY)

    async def _connect_once(self):
        self.ws = await websockets.connect(
            self.ws_url,
            ping_interval=None,
            max_size=16 * 1024 * 1024,
            create_connection=LenientClientConnection,
        )
        self.connected = True
        logger.info("[WS] Connected")
        await self.resubscribe()
        if self.on_connect_callback:
            self.on_connect_callback()
        async for message in self.ws:
            self.on_message_received(message)

    def on_message_received(self, msg):
        if self.on_message_callback:
            self.on_message_callback(msg)

    async def resubscribe(self):
        raise NotImplementedError

    def _schedule(self, coro):
        loop = self._loop
        if loop is None or loop.is_closed() or not self.ws or not self.connected:
            return
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
        else:
            loop.create_task(coro)

    def send_json(self, data: dict):
        loop = self._loop
        if loop is None or loop.is_closed() or not self.ws or not self.connected:
            return
        self._schedule(self._send_json(data))

    async def _send_json(self, data: dict):
        if not self.ws or self.ws.state is CLOSED:
            return
        try:
            await self.ws.send(json.dumps(data))
            logger.debug("[WS] SENT: %s", json.dumps(data))
        except Exception as e:
            logger.error("send error: %s", e)

    def stop(self):
        self._closing = True
        self.reconnect = False
        self.connected = False
        loop = self._loop
        if loop is not None and loop.is_running():
            async def _close():
                if self.ws:
                    try:
                        await self.ws.close()
                    except Exception:
                        pass
                    self.ws = None
                for task in asyncio.all_tasks(loop):
                    task.cancel()
            asyncio.run_coroutine_threadsafe(_close(), loop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

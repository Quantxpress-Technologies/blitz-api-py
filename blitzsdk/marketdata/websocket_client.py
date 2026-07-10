import base64
import json
import logging
import threading
import time
from typing import Optional, Callable

import websocket

from ..common.auth import AuthClient
from ..common.config import Config
from ..proto import marketdata_pb2

logger = logging.getLogger(__name__)


class MarketDataWebSocketClient:
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        self.auth = auth or AuthClient(app_key, user_id)
        self.token = self.auth.get_token()
        self.ws_url = (ws_url or Config.MD_WS_URL) + f"?key={self.token}"
        self.ws: Optional[websocket.WebSocketApp] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self.reconnect = True
        self._closing = False
        self.ping_interval = 30
        self.connected = False
        self._subscribed_ids: set[int] = set()
        self._lock = threading.Lock()
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
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.reconnect and not self._closing:
            try:
                self._connect_async()
            except Exception as e:
                logger.error(f"[MD-WS] Error: {e}")
                if self.on_error_callback:
                    self.on_error_callback(e)
            if self.reconnect and not self._closing:
                time.sleep(5)

    def _connect_async(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever()

    def _resubscribe(self):
        with self._lock:
            ids = list(self._subscribed_ids)
        if ids:
            self._send_json({"action": "subscribe", "instrumentIds": ids})

    def _on_open(self, ws):
        logger.info("[MD-WS] Connected")
        self.connected = True
        self._resubscribe()
        if self.on_connect_callback:
            self.on_connect_callback()
        if not self._heartbeat_thread or not self._heartbeat_thread.is_alive():
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

    def _on_message(self, ws, message):
        if message == "ping":
            return
        try:
            if isinstance(message, str):
                decoded = base64.b64decode(message)
            else:
                decoded = message
            md = marketdata_pb2.MarketDataMessageBase()
            md.ParseFromString(decoded)
            if self.on_message_callback:
                self.on_message_callback(md)
        except Exception as e:
            logger.warning(f"[MD-WS] Parse error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"[MD-WS] Error: {error}")
        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(self, ws, code, msg):
        logger.warning(f"[MD-WS] Closed: {code} {msg}")
        self.connected = False
        if self.on_close_callback:
            self.on_close_callback(code, msg)

    def _heartbeat_loop(self):
        while self.connected and not self._closing:
            time.sleep(self.ping_interval)
            if self.ws and self.ws.sock and self.ws.sock.connected:
                try:
                    self.ws.send("ping")
                except Exception:
                    pass

    def _send_json(self, data: dict):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(data))

    def subscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_ids.add(iid)
        self._send_json({"action": "subscribe", "instrumentIds": instrument_ids})

    def unsubscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_ids.discard(iid)
        self._send_json({"action": "unsubscribe", "instrumentIds": instrument_ids})

    def stop(self):
        self._closing = True
        self.reconnect = False
        self.connected = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

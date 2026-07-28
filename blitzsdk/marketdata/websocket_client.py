import base64
import json
import logging
import ssl
import threading
import time
from typing import Optional

import websocket

from ..common.base_ws_client import BaseWebSocketClient
from ..common.config import Config
from ..common.auth import AuthClient
from ..proto import marketdata_pb2
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class MarketDataWebSocketClient(BaseWebSocketClient):
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        final_url = (ws_url or Config.MD_WS_URL) + "?" + urlencode({"key": ""})
        super().__init__(app_key, user_id, final_url, auth)
        self.ws_url = (ws_url or Config.MD_WS_URL) + "?" + urlencode({"key": self.token})
        self._heartbeat_thread: Optional[threading.Thread] = None
        self.ping_interval = 30
        self._subscribed_ids: set[int] = set()

    def _connect_impl(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def _on_open(self, ws):
        self._on_connected()
        if not self._heartbeat_thread or not self._heartbeat_thread.is_alive():
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

    def _on_message(self, ws, message):
        if message == "ping":
            return
        try:
            decoded = base64.b64decode(message) if isinstance(message, str) else message
            md = marketdata_pb2.MarketDataMessageBase()
            md.ParseFromString(decoded)
            self._on_message_received(md)
        except Exception as e:
            logger.warning(f"[MD-WS] Parse error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"[MD-WS] Error: {error}")
        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(self, ws, code, msg):
        logger.warning(f"[MD-WS] Closed: {code} {msg}")
        self._on_closed(code, msg)

    def _heartbeat_loop(self):
        while self.connected and not self._closing:
            time.sleep(self.ping_interval)
            if self.ws and self.ws.sock and self.ws.sock.connected:
                try:
                    self.ws.send("ping")
                except Exception:
                    pass

    def _resubscribe(self):
        with self._lock:
            ids = list(self._subscribed_ids)
        if ids:
            self._send_json({"action": "subscribe", "instrumentIds": ids})

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

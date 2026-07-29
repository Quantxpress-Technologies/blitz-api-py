import base64
import json
import logging
import ssl

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
        self._subscribed_ids: set[int] = set()

    def connect_impl(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_open(self, ws):
        self.on_connected()

    def on_message(self, ws, message):
        if message == "ping":
            return
        try:
            decoded = base64.b64decode(message) if isinstance(message, str) else message
            md = marketdata_pb2.MarketDataMessageBase()
            md.ParseFromString(decoded)
            self.on_message_received(md)
        except Exception as e:
            logger.warning("Parse error: %s", e)

    def on_error(self, ws, error):
        if self.on_error_callback:
            self.on_error_callback(error)

    def on_close(self, ws, code, msg):
        self.on_closed(code, msg)

    def resubscribe(self):
        with self._lock:
            ids = list(self._subscribed_ids)
        if ids:
            self.send_json({"action": "subscribe", "instrumentIds": ids})

    def send_json(self, data: dict):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error("send error: %s", e)

    def subscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_ids.add(iid)
        self.send_json({"action": "subscribe", "instrumentIds": instrument_ids})

    def unsubscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_ids.discard(iid)
        self.send_json({"action": "unsubscribe", "instrumentIds": instrument_ids})
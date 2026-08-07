import base64
import json
import logging
from urllib.parse import urlencode

from ..common.base_ws_client import BaseWebSocketClient
from ..common.config import Config
from ..common.auth import AuthClient
from ..proto import marketdata_pb2

logger = logging.getLogger(__name__)


class MarketDataWebSocketClient(BaseWebSocketClient):
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        final_url = (ws_url or Config.MD_WS_URL) + "?" + urlencode({"key": ""})
        super().__init__(app_key, user_id, final_url, auth)
        self.ws_url = (ws_url or Config.MD_WS_URL) + "?" + urlencode({"key": self.token})
        self._subscribed_ids: set[int] = set()

    async def resubscribe(self):
        with self._lock:
            ids = list(self._subscribed_ids)
        if ids:
            await self._send_json({"action": "subscribe", "instrumentIds": ids})

    def on_message_received(self, message):
        if message == "ping":
            return
        try:
            decoded = base64.b64decode(message) if isinstance(message, str) else message
            md = marketdata_pb2.MarketDataMessageBase()
            md.ParseFromString(decoded)
            super().on_message_received(md)
        except Exception as e:
            logger.warning("Parse error: %s", e)

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

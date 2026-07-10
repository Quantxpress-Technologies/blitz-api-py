import json
import logging
import threading
import time
from typing import Optional, Callable

import websocket

from ..common.config import Config
from ..common.auth import AuthClient

logger = logging.getLogger(__name__)

ACTION_CODES = {
    "OrderSubscribe": [70000],
    "OrderUnsubscribe": [70000],
    "StatisticSubscribe": [50000],
    "StatisticUnsubscribe": [50000],
    "StrategyStatisticSubscribe": [80000],
    "StrategyStatisticUnsubscribe": [80000],
    "InstrumentStatisticSubscribe": [90000],
    "InstrumentStatisticUnsubscribe": [90000],
    "AllSubscribe": [50000, 70000, 80000, 90000],
    "AllUnsubscribe": [50000, 70000, 80000, 90000],
}


class InteractiveWebSocketClient:
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        self.auth = auth or AuthClient(app_key, user_id)
        self.token = self.auth.get_token()
        self.ws_url = (ws_url or Config.WS_URL) + f"?access_token={self.token}"
        self.ws: Optional[websocket.WebSocket] = None
        self._thread: Optional[threading.Thread] = None
        self.reconnect = True
        self._closing = False
        self.connected = False
        self._subscribed_actions: set[str] = set()
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
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.reconnect and not self._closing:
            try:
                self._connect()
            except Exception as e:
                logger.error(f"[I-WS] Error: {e}")
                if self.on_error_callback:
                    self.on_error_callback(e)
            if self.reconnect and not self._closing:
                time.sleep(5)

    def _connect(self):
        self.ws = websocket.create_connection(self.ws_url, timeout=30)
        self.connected = True
        logger.info("[I-WS] Connected")
        self._resubscribe()
        if self.on_connect_callback:
            self.on_connect_callback()

        self.ws.settimeout(5)
        while self.reconnect and not self._closing:
            try:
                raw = self.ws.recv()
                if raw == "ping":
                    continue
                try:
                    msg = json.loads(raw)
                    if self.on_message_callback:
                        self.on_message_callback(msg)
                except json.JSONDecodeError:
                    logger.warning(f"[I-WS] JSON parse error")
            except websocket.WebSocketTimeoutException:
                logger.debug("[I-WS] recv timeout (no data)")
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                if not self._closing:
                    logger.error(f"[I-WS] recv error: {e}")
                break

        self.connected = False
        try:
            self.ws.close()
        except Exception:
            pass
        logger.info("[I-WS] Disconnected")
        if self.on_close_callback:
            self.on_close_callback(None, "Connection closed")

    def _resubscribe(self):
        with self._lock:
            acts = list(self._subscribed_actions)
        for a in acts:
            self._send_internal({"action": a})

    def _send_internal(self, data: dict):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"[I-WS] send error: {e}")

    def subscribe_action(self, action: str):
        if action not in ACTION_CODES:
            logger.warning(f"[I-WS] Unknown action: {action}")
            return
        with self._lock:
            self._subscribed_actions.add(action)
        self._send_internal({"action": action})

    def unsubscribe_action(self, action: str):
        unsub = action.replace("Subscribe", "Unsubscribe")
        with self._lock:
            self._subscribed_actions.discard(action)
        self._send_internal({"action": unsub})

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

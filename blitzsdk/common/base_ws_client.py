import logging
import threading
from typing import Optional, Callable

from .auth import AuthClient

logger = logging.getLogger(__name__)


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
        self._reconnect_timer: Optional[threading.Timer] = None
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
        threading.Thread(target=self.run, daemon=True).start()

    def schedule_reconnect(self):
        if self.reconnect and not self._closing:
            self._reconnect_timer = threading.Timer(5.0, self.start)
            self._reconnect_timer.daemon = True
            self._reconnect_timer.start()

    def run(self):
        try:
            self.connect_impl()
        except Exception as e:
            logger.error("[WS] Error: %s", e)
            if self.on_error_callback:
                self.on_error_callback(e)
            self.schedule_reconnect()

    def connect_impl(self):
        raise NotImplementedError

    def on_connected(self):
        self.connected = True
        logger.info("[WS] Connected")
        self.resubscribe()
        if self.on_connect_callback:
            self.on_connect_callback()

    def on_message_received(self, msg):
        if self.on_message_callback:
            self.on_message_callback(msg)

    def on_closed(self, code, msg):
        self.connected = False
        if self.on_close_callback:
            self.on_close_callback(code, msg)
        self.schedule_reconnect()

    def resubscribe(self):
        raise NotImplementedError

    def send_json(self, data: dict):
        raise NotImplementedError

    def stop(self):
        self._closing = True
        self.reconnect = False
        self.connected = False
        if self._reconnect_timer:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None
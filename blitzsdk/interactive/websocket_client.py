import json
import logging
import ssl
import threading
from typing import Optional
from urllib.parse import urlencode

import websocket._http as _ws_http
import websocket._handshake as _ws_handshake
from websocket._http import recv_line
from websocket._logging import trace
from websocket._exceptions import WebSocketException


def patch_read_headers():
    def patched_read_headers(sock):
        status = None
        status_message = None
        headers = {}
        last_key = None
        trace("--- response header ---")
        for raw in iter(lambda: recv_line(sock), b""):
            if raw in (b"\r\n", b"\n"):
                break
            decoded = raw.decode("utf-8")
            trace(decoded.rstrip("\r\n"))
            stripped = decoded.strip()
            if decoded[0:1] in (" ", "\t"):
                if last_key and stripped:
                    headers[last_key] = headers[last_key] + " " + stripped
                continue
            if not status:
                parts = stripped.split(" ", 2)
                status = int(parts[1])
                if len(parts) > 2:
                    status_message = parts[2]
            else:
                kv = stripped.split(":", 1)
                if len(kv) != 2:
                    raise WebSocketException("Invalid header")
                k, v = kv
                kl = k.lower()
                v = v.strip()
                if kl == "set-cookie" and headers.get("set-cookie"):
                    headers["set-cookie"] += "; " + v
                else:
                    headers[kl] = v
                last_key = kl
        trace("-----------------------")
        return status, headers, status_message

    _ws_http.read_headers = patched_read_headers
    _ws_handshake.read_headers = patched_read_headers


patch_read_headers()

import websocket

from ..common.base_ws_client import BaseWebSocketClient
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


class InteractiveWebSocketClient(BaseWebSocketClient):
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        final_url = (ws_url or Config.WS_URL) + "?" + urlencode({"access_token": ""})
        super().__init__(app_key, user_id, final_url, auth)
        self.ws_url = (ws_url or Config.WS_URL) + "?" + urlencode({"access_token": self.token})
        self._subscribed_actions: set[str] = set()
        self._subscribed_instruments: set[int] = set()
        self._heartbeat_timer: Optional[threading.Timer] = None
        self._ping_interval = 30

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
        logger.info("[I-WS] Connected")
        self.on_connected()
        self.start_heartbeat()

    def on_message(self, ws, message):
        if message == "ping":
            return
        try:
            msg = json.loads(message)
            mc = msg.get("MessageCode", msg.get("messageCode", "?"))
            logger.debug("[I-WS] RECV code=%s %s", mc, json.dumps(msg, default=str)[:2000])
            self.on_message_received(msg)
        except json.JSONDecodeError:
            logger.warning("Non-JSON message: %s", message[:200])

    def on_error(self, ws, error):
        logger.error("Error: %s", error)
        if self.on_error_callback:
            self.on_error_callback(error)

    def on_close(self, ws, close_status_code, close_msg):
        self.stop_heartbeat()
        self.on_closed(close_status_code, close_msg)

    def start_heartbeat(self):
        self.stop_heartbeat()
        self._heartbeat_timer = threading.Timer(self._ping_interval, self.send_heartbeat)
        self._heartbeat_timer.daemon = True
        self._heartbeat_timer.start()

    def stop_heartbeat(self):
        if self._heartbeat_timer:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None

    def send_heartbeat(self):
        if self.connected and not self._closing:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                try:
                    self.ws.send("ping")
                except Exception:
                    pass
            if self.connected and not self._closing:
                self.start_heartbeat()

    def resubscribe(self):
        with self._lock:
            acts = list(self._subscribed_actions)
            insts = list(self._subscribed_instruments)
        for a in acts:
            self.send_json({"action": a})
        if insts:
            self.send_json({"action": "subscribe", "instrumentIds": insts})

    def send_json(self, data: dict):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                payload = json.dumps(data)
                self.ws.send(payload)
                logger.debug("[I-WS] SENT: %s", json.dumps(data))
            except Exception as e:
                logger.error("send error: %s", e)

    def subscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_instruments.add(iid)
        self.send_json({"action": "subscribe", "instrumentIds": instrument_ids})

    def unsubscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_instruments.discard(iid)
        self.send_json({"action": "unsubscribe", "instrumentIds": instrument_ids})

    def subscribe_action(self, action: str):
        if action not in ACTION_CODES:
            logger.warning("Unknown action: %s", action)
            return
        with self._lock:
            self._subscribed_actions.add(action)
        self.send_json({"action": action})

    def unsubscribe_action(self, action: str):
        unsub = action.replace("Subscribe", "Unsubscribe")
        with self._lock:
            self._subscribed_actions.discard(action)
        self.send_json({"action": unsub})
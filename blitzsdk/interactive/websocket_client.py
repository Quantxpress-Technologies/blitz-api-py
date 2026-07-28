import json
import logging
import ssl
import threading
import time
from typing import Optional
from urllib.parse import urlencode

import websocket._http as _ws_http
import websocket._handshake as _ws_handshake
from websocket._http import recv_line
from websocket._logging import trace
from websocket._exceptions import WebSocketException

def _patch_read_headers():
    def patched_read_headers(sock):
        status = None
        status_message = None
        headers = {}
        last_key = None
        trace("--- response header ---")
        while True:
            raw = recv_line(sock)
            if not raw:
                break
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

_patch_read_headers()

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
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._ping_interval = 30

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
        logger.info("[I-WS] Connected")
        self.connected = True
        self._on_connected()
        if not self._heartbeat_thread or not self._heartbeat_thread.is_alive():
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

    def _on_message(self, ws, message):
        if message == "ping":
            return
        try:
            msg = json.loads(message)
            mc = msg.get("MessageCode", msg.get("messageCode", "?"))
            logger.info("[I-WS] RECV code=%s %s", mc, json.dumps(msg, default=str)[:2000])
            self._on_message_received(msg)
        except json.JSONDecodeError:
            logger.warning("[I-WS] Non-JSON: %s", message[:200])

    def _on_error(self, ws, error):
        logger.error(f"[I-WS] Error: {error}")
        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"[I-WS] Closed: {close_status_code} {close_msg}")
        self.connected = False
        if self.on_close_callback:
            self.on_close_callback(close_status_code, close_msg)

    def _heartbeat_loop(self):
        while self.connected and not self._closing:
            time.sleep(self._ping_interval)
            if self.ws and self.ws.sock and self.ws.sock.connected:
                try:
                    self.ws.send("ping")
                except Exception:
                    pass

    def _resubscribe(self):
        with self._lock:
            acts = list(self._subscribed_actions)
            insts = list(self._subscribed_instruments)
        for a in acts:
            self._send_json({"action": a})
        if insts:
            self._send_json({"action": "subscribe", "instrumentIds": insts})

    def _send_json(self, data: dict):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                payload = json.dumps(data)
                self.ws.send(payload)
                logger.info(f"[I-WS] SENT: {json.dumps(data)}")
            except Exception as e:
                logger.error(f"[I-WS] send error: {e}")

    def subscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_instruments.add(iid)
        self._send_json({"action": "subscribe", "instrumentIds": instrument_ids})

    def unsubscribe(self, instrument_ids: list[int]):
        with self._lock:
            for iid in instrument_ids:
                self._subscribed_instruments.discard(iid)
        self._send_json({"action": "unsubscribe", "instrumentIds": instrument_ids})

    def subscribe_action(self, action: str):
        if action not in ACTION_CODES:
            logger.warning(f"[I-WS] Unknown action: {action}")
            return
        with self._lock:
            self._subscribed_actions.add(action)
        self._send_json({"action": action})

    def unsubscribe_action(self, action: str):
        unsub = action.replace("Subscribe", "Unsubscribe")
        with self._lock:
            self._subscribed_actions.discard(action)
        self._send_json({"action": unsub})

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

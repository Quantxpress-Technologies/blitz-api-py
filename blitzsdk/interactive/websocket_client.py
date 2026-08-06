import asyncio
import json
import logging
from typing import Optional
from urllib.parse import urlencode

from websockets.protocol import CLOSED

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

HEARTBEAT_INTERVAL = 30


class InteractiveWebSocketClient(BaseWebSocketClient):
    def __init__(self, app_key: str, user_id: str, ws_url: str | None = None, auth: AuthClient | None = None):
        final_url = (ws_url or Config.WS_URL) + "?" + urlencode({"access_token": ""})
        super().__init__(app_key, user_id, final_url, auth)
        self.ws_url = (ws_url or Config.WS_URL) + "?" + urlencode({"access_token": self.token})
        self._subscribed_actions: set[str] = set()
        self._subscribed_instruments: set[int] = set()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def resubscribe(self):
        with self._lock:
            acts = list(self._subscribed_actions)
            insts = list(self._subscribed_instruments)
        for a in acts:
            await self._send_json({"action": a})
        if insts:
            await self._send_json({"action": "subscribe", "instrumentIds": insts})
        self._start_heartbeat()

    def _start_heartbeat(self):
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        loop = self._loop
        if loop is None or loop.is_closed() or not loop.is_running():
            return
        self._heartbeat_task = asyncio.run_coroutine_threadsafe(self._heartbeat(), loop)

    async def _heartbeat(self):
        while self.connected and not self._closing:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if self.connected and not self._closing:
                await self._send_text("ping")

    async def _send_text(self, text: str):
        if not self.ws or self.ws.state is CLOSED:
            return
        try:
            await self.ws.send(text)
        except Exception as e:
            logger.error("send error: %s", e)

    def on_message_received(self, message):
        if message == "ping":
            return
        try:
            msg = json.loads(message)
            mc = msg.get("MessageCode", msg.get("messageCode", "?"))
            logger.debug("[I-WS] RECV code=%s %s", mc, json.dumps(msg, default=str)[:2000])
            super().on_message_received(msg)
        except json.JSONDecodeError:
            logger.warning("Non-JSON message: %s", str(message)[:200])

    # def subscribe(self, instrument_ids: list[int]):
    #     with self._lock:
    #         for iid in instrument_ids:
    #             self._subscribed_instruments.add(iid)
    #     self.send_json({"action": "subscribe", "instrumentIds": instrument_ids})

    # def unsubscribe(self, instrument_ids: list[int]):
    #     with self._lock:
    #         for iid in instrument_ids:
    #             self._subscribed_instruments.discard(iid)
    #     self.send_json({"action": "unsubscribe", "instrumentIds": instrument_ids})

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

import json
import sys
import os
import threading
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveWebSocketClient

_LOG_FILE = os.path.join(os.path.dirname(__file__), "interactive_ws.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging WebSocket data to {_LOG_FILE}")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg

connect_count = 0
close_events = []


def run():
    global connect_count, close_events
    client = InteractiveWebSocketClient(
        app_key=_conn["AppKey"],
        user_id=_conn["UserId"],
    )

    received = []

    print("--- Interactive WebSocket Tests ---")

    def on_message(data):
        received.append(data)
        mc = data.get("MessageCode", data.get("messageCode", "?"))
        msg = json.dumps(data, default=str)
        _log.info("[WS] code=%s %s", mc, msg)
        print(f"  [WS] code={mc} {msg}")

    def on_connect():
        global connect_count
        connect_count += 1
        _log.info("[WS] Connected (connect_count=%s)", connect_count)
        print(f"  [WS] Connected (connect_count={connect_count})")
        client.subscribe_action("AllSubscribe")
        _log.info("[WS] AllSubscribe sent")
        print("  [WS] AllSubscribe sent")

    def on_close(code, msg):
        close_events.append((code, msg))
        _log.info("[WS] Closed: code=%s msg=%s", code, msg)
        print(f"  [WS] Closed: code={code} msg={msg}")

    client.set_on_message(on_message)
    client.set_on_connect(on_connect)
    client.set_on_close(on_close)

    client.start()

    try:
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    finally:
        client.stop()
        _log.info("[INFO] Received %s messages", len(received))
        _log.info("[INFO] Connect count: %s", connect_count)
        _log.info("[INFO] Close events: %s", len(close_events))
        print(f"  [INFO] Received {len(received)} messages")
        print(f"  [INFO] Connect count: {connect_count}")
        print(f"  [INFO] Close events: {len(close_events)}")
    return 0


if __name__ == "__main__":
    sys.exit(run())

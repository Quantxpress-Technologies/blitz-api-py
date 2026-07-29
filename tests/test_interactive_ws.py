import json
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveWebSocketClient

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["environments"][_cfg.get("active", "local")]

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
        print(f"  [WS] code={mc} {json.dumps(data, default=str)[:200]}")

    def on_connect():
        global connect_count
        connect_count += 1
        print(f"  [WS] Connected (connect_count={connect_count})")
        client.subscribe_action("AllSubscribe")
        print("  [WS] AllSubscribe sent")

    def on_close(code, msg):
        close_events.append((code, msg))
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
        print(f"  [INFO] Received {len(received)} messages")
        print(f"  [INFO] Connect count: {connect_count}")
        print(f"  [INFO] Close events: {len(close_events)}")
    return 0


if __name__ == "__main__":
    sys.exit(run())

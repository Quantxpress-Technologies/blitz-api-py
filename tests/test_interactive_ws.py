import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveWebSocketClient

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["environments"][_cfg.get("active", "local")]


def run():
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
        print("  [WS] Connected")
        client.subscribe_action("AllSubscribe")
        print("  [WS] AllSubscribe sent")

    def on_close(code, msg):
        print(f"  [WS] Closed: {code} {msg}")

    client.set_on_message(on_message)
    client.set_on_connect(on_connect)
    client.set_on_close(on_close)

    client.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    client.stop()
    print(f"  [INFO] Received {len(received)} messages")
    return 0


if __name__ == "__main__":
    sys.exit(run())

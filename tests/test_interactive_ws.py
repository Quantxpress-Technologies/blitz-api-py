import json
import sys
import os
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveWebSocketClient

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["Connection"]

running = True


def run():
    global running
    client = InteractiveWebSocketClient(
        app_key=_conn["AppKey"],
        user_id=_conn["UserId"],
    )

    print("--- Interactive WebSocket Listener ---")
    print("  Place an order (test_interactive_api.py) in another terminal")
    print("  Press Ctrl+C to stop\n")

    def on_message(data):
        print(json.dumps(data, indent=2))

    def on_connect():
        print("  [WS] Connected, subscribing...")
        client.subscribe_action("AllSubscribe")
        print("  [WS] subscribed Actions")

    def on_close(code, msg):
        print(f"  [WS] Closed: {code} {msg}")

    client.set_on_message(on_message)
    client.set_on_connect(on_connect)
    client.set_on_close(on_close)

    def handle_signal(sig, frame):
        global running
        print("\n  Shutting down...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)

    client.start()
    import time
    time.sleep(2)

    if not client.connected:
        print("  [FAIL] WebSocket did not connect")
        return 1

    while running:
        time.sleep(1)

    client.stop()
    print("  Disconnected")
    return 0


if __name__ == "__main__":
    sys.exit(run())

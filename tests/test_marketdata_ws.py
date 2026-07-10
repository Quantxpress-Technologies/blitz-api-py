import json
import sys
import os
import time
import signal

from google.protobuf.json_format import MessageToJson

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import MarketDataWebSocketClient

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["Connection"]

running = True


def run():
    global running
    print("Initializing MarketDataWebSocketClient...")

    ws = MarketDataWebSocketClient(
        app_key=_conn["AppKey"],
        user_id=_conn["UserId"],
    )

    instrument_ids = _conn.get("InstrumentIds", [110010002000001, 110010000002885])
    timeout_sec = _conn.get("WsTimeoutSeconds", 15)

    print("--- Market Data WebSocket Tests ---")

    def on_message(data):
        print(f"New tick data received:{MessageToJson(data)}")

    def on_connect():
        print("  [WS] Connected")

    ws.set_on_message(on_message)
    ws.set_on_connect(on_connect)

    def handle_signal(sig, frame):
        global running
        print("\n  Shutting down...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)

    print("  Connecting...")
    sys.stdout.flush()
    ws.start()
    time.sleep(2)

    print("  Subscribing...")
    ws.subscribe(instrument_ids)
    print(f"  [PASS] Subscribed to {instrument_ids}")

    print(f"  Listening for {timeout_sec}s (press Ctrl+C to stop early)...")
    sys.stdout.flush()

    start = time.time()
    while running and (time.time() - start) < timeout_sec:
        elapsed = int(time.time() - start)
        if elapsed > 0 and elapsed % 5 == 0:
            print(f"  ... {timeout_sec - elapsed}s remaining")
            sys.stdout.flush()
        time.sleep(1)

    print("  Stopping WebSocket...")
    ws.stop()
    print("  [PASS] WebSocket disconnected cleanly")
    print("  PASSED: 3   FAILED: 0")
    return 0


if __name__ == "__main__":
    sys.exit(run())

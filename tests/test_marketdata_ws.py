import json
import sys
import os
import time
import signal
import threading
import logging

from google.protobuf.json_format import MessageToJson

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import MarketDataWebSocketClient

_LOG_FILE = os.path.join(os.path.dirname(__file__), "marketdata_ws.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging WebSocket ticks to {_LOG_FILE}")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["environments"][_cfg.get("active", "local")]

running = True
connect_count = 0
close_events = []


def run():
    global running, connect_count, close_events
    print("Initializing MarketDataWebSocketClient...")

    ws = MarketDataWebSocketClient(
        app_key=_conn["AppKey"],
        user_id=_conn["UserId"],
    )

    instrument_ids = _conn.get("InstrumentIds", [110010002000001, 110010000002885])

    print("--- Market Data WebSocket Tests ---")

    tick_count = 0

    def on_message(data):
        nonlocal tick_count
        tick_count += 1
        msg = MessageToJson(data)
        _log.info("[TICK %s] %s", tick_count, msg)
        print(f"  [TICK {tick_count}] {msg[:200]}")

    def on_connect():
        global connect_count
        connect_count += 1
        _log.info("[WS] Connected (connect_count=%s)", connect_count)
        print(f"  [WS] Connected (connect_count={connect_count})")

    def on_close(code, msg):
        close_events.append((code, msg))
        _log.info("[WS] Closed: code=%s msg=%s", code, msg)
        print(f"  [WS] Closed: code={code} msg={msg}")

    ws.set_on_message(on_message)
    ws.set_on_connect(on_connect)
    ws.set_on_close(on_close)

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
    _log.info("[WS] Subscribed to %s", instrument_ids)
    print(f"  [PASS] Subscribed to {instrument_ids}")

    print("  Listening (press Ctrl+C to stop)...")
    sys.stdout.flush()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        ws.stop()
        _log.info("[INFO] Total ticks: %s", tick_count)
        _log.info("[INFO] Connect count: %s", connect_count)
        _log.info("[INFO] Close events: %s", len(close_events))
        print(f"  [INFO] Total ticks: {tick_count}")
        print(f"  [INFO] Connect count: {connect_count}")
        print(f"  [INFO] Close events: {len(close_events)}")
        print("  [PASS] WebSocket test completed")
    return 0


if __name__ == "__main__":
    run()

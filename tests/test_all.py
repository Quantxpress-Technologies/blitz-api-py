import json
import sys
import os
import time
import logging
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_LOG_FILE = os.path.join(os.path.dirname(__file__), "all_tests.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging to {_LOG_FILE}")

from blitzsdk import InteractiveApiClient, MarketDataApiClient
from blitzsdk import InteractiveWebSocketClient, MarketDataWebSocketClient
from blitzsdk.interactive.models import OrderRequest
from blitzsdk.marketdata.instrument_manager import InstrumentManager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _conn = json.load(f)

# How long to listen on each WebSocket before moving on (seconds).
WS_LISTEN_SECONDS = float(_conn.get("WsListenSeconds", 20))

_iapi: InteractiveApiClient | None = None
_mdapi: MarketDataApiClient | None = None


def get_iapi():
    global _iapi
    if _iapi is None:
        _iapi = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _iapi


def get_mdapi():
    global _mdapi
    if _mdapi is None:
        _mdapi = MarketDataApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _mdapi


def print_response(data):
    if isinstance(data, dict) or isinstance(data, list):
        _log.info("response=%s", json.dumps(data, indent=2, default=str))
        print(json.dumps(data, indent=2, default=str))
    else:
        _log.info("response=%s", data)
        print(data)


_ORDER = next(i for i in _conn["Instruments"] if i.get("symbol"))


def resolve_instrument_id(symbol: str) -> int:
    if not InstrumentManager._cache:
        InstrumentManager.load()
    full = f"NSECM|{symbol}" if "|" not in symbol else symbol
    instrument_id = InstrumentManager.resolve(symbol=full)
    _log.info("[INST] Resolved %s -> %s", full, instrument_id)
    print(f"  [INFO] Resolved {full} -> {instrument_id}")
    return instrument_id


def place_order():
    instrument_id = resolve_instrument_id(_ORDER["symbol"])
    order = OrderRequest(
        instrument_id=instrument_id,
        symbol=f"NSECM|{_ORDER['symbol']}",
        quantity=1,
        price=_conn["DemoOrderPrice"],
        order_side="BUY",
        order_type="LIMIT",
        product="MIS",
        tif="GFD",
        gtd_date=time.strftime("%Y-%m-%d"),
        client_id=_conn["ClientId"],
    )
    r = get_iapi().place_order(order)
    js = r if isinstance(r, dict) else {}
    data = js.get("data", {}) if isinstance(js, dict) else {}
    bid = data.get("blitzOrderId") or data.get("blitz_order_id")
    return r, bid


def run_interactive_api():
    client = get_iapi()
    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            _log.info("[PASS] %s", name)
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            _log.error("[FAIL] %s: %s", name, e)
            failed += 1

    print("--- Interactive API Tests ---")

    def get_orders():
        print_response(client.get_orders())

    def get_open_orders():
        print_response(client.get_open_orders())

    def get_positions():
        print_response(client.get_positions())

    def get_trades():
        print_response(client.get_trades())

    def get_statistics():
        print_response(client.get_statistics())

    def get_statistics_by_instance():
        print_response(client.get_statistics_by_instance("Manual Trading", "NSECM|RELIANCE"))

    def api_place_order():
        r, _ = place_order()
        print_response(r)

    def get_order():
        r, bid = place_order()
        if bid:
            print_response(client.get_order_by_blitz_id(bid))

    def modify_order():
        r, bid = place_order()
        if bid:
            r = client.modify_order({
                "BlitzOrderId": bid,
                "ModifiedOrderQuantity": 1,
                "Price": _conn["DemoOrderPrice"],
                "OrderType": "LIMIT",
                "InstrumentId": _ORDER["id"],
                "Symbol": None,
                "DisclosedQuantity": 0,
                "StopPrice": 0,
                "TIF": "GFD",
                "TiF_GTD_Date": time.strftime("%Y-%m-%d"),
            })
            print_response(r)

    def cancel_order():
        r, bid = place_order()
        if bid:
            print_response(client.cancel_order(_ORDER["id"], bid))

    def send_signals():
        r = client.send_signals([{
            "SourceStrategy": "Bull8.AmberX1",
            "DestinationStrategy": "Matrix",
            "SourceSID": "Bull8_SINGLE_Matrix",
            "InstanceRunningMode": "Started",
            "GlobalAction": "Signal",
            "Instruments": [{
                "ExchangeSegment": "NSEFO",
                "InstrumentName": "NIFTY10FEB2625550PE",
                "Action": "ENTERLONG",
                "Lot": "27",
                "TimeStamp": time.strftime("%d-%m-%Y %H:%M:%S"),
                "InfoText": "Test signal",
            }]
        }])
        print_response(r)

    test("GetOrders", get_orders)
    test("GetOpenOrders", get_open_orders)
    test("GetPositions", get_positions)
    test("GetTrades", get_trades)
    test("GetStatistics", get_statistics)
    test("GetStatisticsByInstance", get_statistics_by_instance)
    test("PlaceOrder", api_place_order)
    test("GetOrderByBlitzId", get_order)
    test("ModifyOrder", modify_order)
    test("CancelOrder", cancel_order)
    test("SendSignals", send_signals)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    _log.info("Interactive API: PASSED=%s FAILED=%s", passed, failed)
    return failed


def run_marketdata_api():
    client = get_mdapi()
    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            _log.info("[PASS] %s", name)
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            _log.error("[FAIL] %s: %s", name, e)
            failed += 1

    instrument_ids = [i["id"] for i in _conn["Instruments"]]
    instrument_id = instrument_ids[0]
    InstrumentManager.load()
    name_symbols = [InstrumentManager._id_cache[iid] for iid in instrument_ids]
    expiry = _conn.get("TestExpiry", "2026-07-07")

    print("--- Market Data API Tests ---")

    def get_instrument_by_id():
        print_response(client.get_instrument_by_id(instrument_id))

    def get_instrument_by_symbol():
        print_response(client.get_instrument_by_symbol(name_symbols[0]))

    def get_ltp_by_ids():
        print_response(client.get_ltp([instrument_id]))

    def get_ltp_by_names():
        ids = InstrumentManager.resolve_ids(name_symbols)
        print_response(client.get_ltp(ids))

    def get_option_chain():
        print_response(client.get_option_chain("NIFTY", expiry))

    def get_quote_by_ids():
        print_response(client.get_quote([instrument_id]))

    def get_quote_by_names():
        ids = InstrumentManager.resolve_ids(name_symbols)
        print_response(client.get_quote(ids))

    def get_historical_data():
        print_response(client.get_historical_data("RELIANCE", "D"))

    def instrument_count():
        InstrumentManager.load()
        print(f"       instruments loaded: {InstrumentManager.count()}")

    test("GetInstrumentById", get_instrument_by_id)
    test("GetInstrumentBySymbol", get_instrument_by_symbol)
    test("GetLTPByIds", get_ltp_by_ids)
    test("GetLTPByNames", get_ltp_by_names)
    test("GetOptionChain", get_option_chain)
    test("GetQuoteByIds", get_quote_by_ids)
    test("GetQuoteByNames", get_quote_by_names)
    test("GetHistoricalData", get_historical_data)
    test("InstrumentCount", instrument_count)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    _log.info("Market Data API: PASSED=%s FAILED=%s", passed, failed)
    return failed


def run_interactive_ws():
    print("--- Interactive WebSocket Tests ---")
    _log.info("--- Interactive WebSocket Tests ---")
    received = []
    close_events = []
    connect_count = 0
    ok = True

    client = InteractiveWebSocketClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])

    def on_message(data):
        received.append(data)
        mc = data.get("MessageCode", data.get("messageCode", "?"))
        msg = json.dumps(data, default=str)
        _log.info("[I-WS] code=%s %s", mc, msg)
        print(f"  [WS] code={mc} {msg[:160]}")

    def on_connect():
        nonlocal connect_count
        connect_count += 1
        _log.info("[I-WS] Connected (connect_count=%s)", connect_count)
        print(f"  [WS] Connected (connect_count={connect_count})")
        client.subscribe_action("AllSubscribe")
        _log.info("[I-WS] AllSubscribe sent")
        print("  [WS] AllSubscribe sent")

    def on_close(code, msg):
        close_events.append((code, msg))
        _log.info("[I-WS] Closed: code=%s msg=%s", code, msg)
        print(f"  [WS] Closed: code={code} msg={msg}")

    client.set_on_message(on_message)
    client.set_on_connect(on_connect)
    client.set_on_close(on_close)
    client.start()

    try:
        deadline = time.time() + WS_LISTEN_SECONDS
        while time.time() < deadline:
            time.sleep(0.2)
            if received:
                break
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()

    codes = sorted({str(d.get("MessageCode", d.get("messageCode", "?"))) for d in received})
    _log.info("[I-WS] Received %s messages, connect_count=%s, codes=%s", len(received), connect_count, codes)
    print(f"  [INFO] Interactive WS received {len(received)} messages, connect_count={connect_count}, codes={codes}")

    if connect_count == 0:
        print("  [FAIL] InteractiveWS: never connected")
        _log.error("[FAIL] InteractiveWS: never connected")
        return 1
    if not received:
        print("  [FAIL] InteractiveWS: no messages received")
        _log.error("[FAIL] InteractiveWS: no messages received")
        return 1

    print("  [PASS] InteractiveWS")
    _log.info("[PASS] InteractiveWS")
    return 0


def run_marketdata_ws():
    print("--- Market Data WebSocket Tests ---")
    _log.info("--- Market Data WebSocket Tests ---")
    tick_count = 0
    connect_count = 0
    close_events = []
    ok = True

    ws = MarketDataWebSocketClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    instrument_ids = [i["id"] for i in _conn["Instruments"]]

    def on_message(data):
        nonlocal tick_count
        tick_count += 1
        from google.protobuf.json_format import MessageToJson
        msg = MessageToJson(data)
        _log.info("[MD-TICK %s] %s", tick_count, msg[:2000])
        print(f"  [TICK {tick_count}] {msg[:160]}")

    def on_connect():
        nonlocal connect_count
        connect_count += 1
        _log.info("[MD-WS] Connected (connect_count=%s)", connect_count)
        print(f"  [WS] Connected (connect_count={connect_count})")

    def on_close(code, msg):
        close_events.append((code, msg))
        _log.info("[MD-WS] Closed: code=%s msg=%s", code, msg)
        print(f"  [WS] Closed: code={code} msg={msg}")

    ws.set_on_message(on_message)
    ws.set_on_connect(on_connect)
    ws.set_on_close(on_close)

    ws.start()
    time.sleep(2)
    ws.subscribe(instrument_ids)
    _log.info("[MD-WS] Subscribed to %s", instrument_ids)
    print(f"  [PASS] Subscribed to {instrument_ids}")

    try:
        deadline = time.time() + WS_LISTEN_SECONDS
        while time.time() < deadline:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        ws.stop()

    _log.info("[MD-WS] Total ticks: %s, connect_count=%s", tick_count, connect_count)
    print(f"  [INFO] Market Data WS received {tick_count} ticks, connect_count={connect_count}")

    if connect_count == 0:
        print("  [FAIL] MarketDataWS: never connected")
        _log.error("[FAIL] MarketDataWS: never connected")
        return 1
    if tick_count == 0:
        print("  [FAIL] MarketDataWS: no ticks received")
        _log.error("[FAIL] MarketDataWS: no ticks received")
        return 1

    print("  [PASS] MarketDataWS")
    _log.info("[PASS] MarketDataWS")
    return 0


def main():
    print(f"=== All API + WebSocket Tests (listen {WS_LISTEN_SECONDS}s) ===")
    _log.info("=== All API + WebSocket Tests (listen %ss) ===", WS_LISTEN_SECONDS)

    results = {
        "InteractiveApi": run_interactive_api(),
        "MarketDataApi": run_marketdata_api(),
        "InteractiveWs": run_interactive_ws(),
        "MarketDataWs": run_marketdata_ws(),
    }

    print("\n=== SUMMARY ===")
    _log.info("=== SUMMARY ===")
    for name, rc in results.items():
        status = "PASS" if rc == 0 else "FAIL"
        print(f"  {name}: {status}")
        _log.info("%s: %s", name, status)

    total_failed = sum(1 for rc in results.values() if rc != 0)
    print(f"\n  Overall: {4 - total_failed}/4 suites passed")
    _log.info("Overall: %s/4 suites passed", 4 - total_failed)
    print(f"  Full log: {_LOG_FILE}")
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())

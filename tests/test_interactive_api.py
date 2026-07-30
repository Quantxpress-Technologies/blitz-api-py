import json
import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_LOG_FILE = os.path.join(os.path.dirname(__file__), "interactive_api.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging to {_LOG_FILE}")

from blitzsdk import InteractiveApiClient, MarketDataApiClient
from blitzsdk.interactive.models import OrderRequest

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["environments"][_cfg.get("active", "local")]
_client: InteractiveApiClient | None = None


def _get_client():
    global _client
    if _client is None:
        _client = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _client


def _pp(data):
    raw = data.get("response_text", "")
    js = data.get("response_json")
    _log.info("status=%s raw=(%s chars)", data.get("status_code"), len(raw))
    _log.info("response_json=%s", json.dumps(js, indent=2, default=str) if js is not None else raw)
    print(f"  status={data.get('status_code')} raw=({len(raw)} chars)")
    if js is not None:
        print(json.dumps(js, indent=2))


_last_open_place_price = None

def _place_open_order(client):
    """Place a buy LIMIT below market so it stays open (won't fill). Returns (blitz_id, price)."""
    global _last_open_place_price
    try:
        md = MarketDataApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
        ltp_resp = md.get_ltp([_conn["DemoOrderInstrumentId"]])
        js = ltp_resp.get("response_json", {})
        ltp = _conn["DemoOrderPrice"]
        if isinstance(js, dict):
            for v in js.get("data", {}).values():
                if isinstance(v, dict) and v.get("ltp"):
                    ltp = v["ltp"]
                    break
        price = round(ltp * 0.95, 2)
        _last_open_place_price = price
        order = OrderRequest(
            instrument_id=_conn["DemoOrderInstrumentId"],
            symbol=_conn["DemoOrderSymbol"],
            price=price,
            client_id=_conn["DemoOrderClientId"],
        )
        resp = client.place_order(order)
        js = resp.get("response_json", {})
        if js.get("status") == "success":
            data = js.get("data", {})
            bid = data.get("blitzOrderId") or data.get("blitz_order_id")
            return bid, price
    except Exception as e:
        print(f"       _place_open_order error: {e}")
    return None, None


def _place_demo_order(client):
    """Alias for backward compat - places at configured price (may fill immediately)."""
    try:
        order = OrderRequest(
            instrument_id=_conn["DemoOrderInstrumentId"],
            symbol=_conn["DemoOrderSymbol"],
            price=_conn["DemoOrderPrice"],
            client_id=_conn["DemoOrderClientId"],
        )
        resp = client.place_order(order)
        js = resp.get("response_json", {})
        if js.get("status") == "success":
            data = js.get("data", {})
            return data.get("blitzOrderId") or data.get("blitz_order_id")
    except Exception:
        pass
    return None


def run():
    client = _get_client()
    md_client = MarketDataApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print("--- All API Tests ---")

    def test_get_orders():
        r = client.get_orders()
        _pp(r)

    def test_get_open_orders():
        r = client.get_open_orders()
        _pp(r)

    def test_get_positions():
        r = client.get_positions()
        _pp(r)

    def test_get_trades():
        r = client.get_trades()
        _pp(r)

    def test_place_order():
        order = OrderRequest(
            instrument_id=_conn["DemoOrderInstrumentId"],
            symbol=_conn["DemoOrderSymbol"],
            price=_conn["DemoOrderPrice"],
            client_id=_conn["DemoOrderClientId"],
        )
        r = client.place_order(order)
        _pp(r)

    def test_get_order_by_blitz_id():
        blitz_id = _place_demo_order(client)
        if blitz_id is None:
            print("       skipping (no order placed)")
            return
        r = client.get_order_by_blitz_id(blitz_id)
        _pp(r)

    def test_modify_order():
        blitz_id, placed_price = _place_open_order(client)
        if blitz_id is None:
            print("       skipping (no order placed)")
            return
        modify_price = round(placed_price * 1.01, 2)  # 1% above placed price
        r = client.modify_order({
            "BlitzOrderId": blitz_id,
            "ModifiedOrderQuantity": 1,
            "Price": modify_price,
            "OrderType": "LIMIT",
            "InstrumentId": _conn["DemoOrderInstrumentId"],
            "Symbol": _conn["DemoOrderSymbol"],
            "DisclosedQuantity": 0,
            "StopPrice": 0,
            "TIF": "GFD",
            "TiF_GTD_Date": time.strftime("%Y-%m-%d"),
        })
        _pp(r)

    def test_cancel_order():
        blitz_id, placed_price = _place_open_order(client)
        if blitz_id is None:
            print("       skipping (no order placed)")
            return
        r = client.cancel_order(_conn["DemoOrderInstrumentId"], blitz_id)
        _pp(r)

    def test_send_signals():
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
        _pp(r)

    def test_get_ltp():
        r = md_client.get_ltp([_conn["DemoOrderInstrumentId"]])
        _pp(r)

    def test_get_quote():
        r = md_client.get_quote([_conn["DemoOrderInstrumentId"]])
        _pp(r)

    def test_get_option_chain():
        r = md_client.get_option_chain(symbol="NIFTY", expiry="2026-09-01")
        _pp(r)

    def test_get_historical_data():
        r = md_client.get_historical_data(instrument=_conn["DemoOrderSymbol"], interval="D")
        _pp(r)

    # test("GetOrders", test_get_orders)
    # test("GetOpenOrders", test_get_open_orders)
    # test("GetPositions", test_get_positions)
    # test("GetTrades", test_get_trades)
    # test("PlaceOrder", test_place_order)
    # test("GetOrderByBlitzId", test_get_order_by_blitz_id)
    # test("ModifyOrder", test_modify_order)
    # test("CancelOrder", test_cancel_order)
    test("SendSignals", test_send_signals)
    # test("GetLTP", test_get_ltp)
    # test("GetQuote", test_get_quote)
    # test("GetOptionChain", test_get_option_chain)
    # test("GetHistoricalData", test_get_historical_data)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    return failed


if __name__ == "__main__":
    sys.exit(run())

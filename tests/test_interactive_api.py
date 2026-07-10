import json
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveApiClient
from blitzsdk.interactive.models import OrderRequest

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["Connection"]
_client: InteractiveApiClient | None = None


def _get_client():
    global _client
    if _client is None:
        _client = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _client


def _pp(data):
    raw = data.get("response_text", "")
    js = data.get("response_json")
    print(f"  status={data.get('status_code')} raw=({len(raw)} chars)")
    if js is not None:
        print(json.dumps(js, indent=2))


def _place_demo_order(client):
    order = OrderRequest(
        instrument_id=_conn["DemoOrderInstrumentId"],
        symbol=_conn["DemoOrderSymbol"],
        price=_conn["DemoOrderPrice"],
        client_id=_conn["DemoOrderClientId"],
    )
    resp = client.place_order(order)
    js = resp.get("response_json", {})
    if js.get("status") == "success":
        return js.get("data", {}).get("blitz_order_id")
    return None


def run():
    client = _get_client()
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

    print("--- Interactive API Tests ---")

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
        if blitz_id:
            print(f"       blitz_order_id={blitz_id}")
        r = client.get_order_by_blitz_id(blitz_id)
        _pp(r)

    def test_modify_order():
        blitz_id = _place_demo_order(client)
        if blitz_id:
            print(f"       blitz_order_id={blitz_id}")
        r = client.modify_order({
            "blitzOrderId": blitz_id,
            "modifiedOrderQuantity": 2,
            "price": 10.5,
            "orderType": "LIMIT",
            "instrumentId": _conn["DemoOrderInstrumentId"],
            "symbol": _conn["DemoOrderSymbol"],
            "disclosedQuantity": 0,
            "stopPrice": 0,
            "tif": "GFD",
        })
        _pp(r)

    def test_cancel_order():
        blitz_id = _place_demo_order(client)
        if blitz_id:
            print(f"       blitz_order_id={blitz_id}")
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
                "Action": "BUY",
                "Lot": "27",
                "TimeStamp": time.strftime("%d-%m-%Y %H:%M:%S"),
                "InfoText": "Test signal",
            }]
        }])
        _pp(r)

    test("GetOrders", test_get_orders)
    # test("GetOpenOrders", test_get_open_orders)
    # test("GetPositions", test_get_positions)
    # test("GetTrades", test_get_trades)
    # test("PlaceOrder", test_place_order)
    # test("GetOrderByBlitzId", test_get_order_by_blitz_id)
    # test("ModifyOrder", test_modify_order)
    # test("CancelOrder", test_cancel_order)
    # test("SendSignals", test_send_signals)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    return failed


if __name__ == "__main__":
    sys.exit(run())

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

from blitzsdk import InteractiveApiClient
from blitzsdk.interactive.models import OrderRequest

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg
_client: InteractiveApiClient | None = None


def get_client():
    global _client
    if _client is None:
        _client = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _client


def print_response(data):
    if isinstance(data, dict) or isinstance(data, list):
        _log.info("response=%s", json.dumps(data, indent=2, default=str))
        print(json.dumps(data, indent=2, default=str))
    else:
        _log.info("response=%s", data)
        print(data)


_ORDER = next(i for i in _conn["Instruments"] if i.get("symbol"))


def place_order():
    """Place one order and return its blitz order id."""
    order = OrderRequest(
        instrument_id=_ORDER["id"],
        symbol=_ORDER["symbol"],
        quantity=1,
        price=_conn["DemoOrderPrice"],
        order_side="BUY",
        order_type="LIMIT",
        product="MIS",
        tif="GFD",
        gtd_date=time.strftime("%Y-%m-%d"),
        client_id=_conn["ClientId"],
    )
    r = get_client().place_order(order)
    js = r if isinstance(r, dict) else {}
    data = js.get("data", {}) if isinstance(js, dict) else {}
    bid = data.get("blitzOrderId") or data.get("blitz_order_id")
    return r, bid


def run():
    client = get_client()
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

    # test("GetOrders", get_orders)
    # test("GetOpenOrders", get_open_orders)
    # test("GetPositions", get_positions)
    # test("GetTrades", get_trades)
    # test("GetStatistics", get_statistics)
    # test("GetStatisticsByInstance", get_statistics_by_instance)
    test("PlaceOrder", api_place_order)
    # test("GetOrderByBlitzId", get_order)
    # test("ModifyOrder", modify_order)
    # test("CancelOrder", cancel_order)
    # test("SendSignals", send_signals)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    return failed


if __name__ == "__main__":
    sys.exit(run())

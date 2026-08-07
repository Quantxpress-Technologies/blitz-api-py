import json
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_LOG_FILE = os.path.join(os.path.dirname(__file__), "marketdata_api.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging to {_LOG_FILE}")

from blitzsdk import MarketDataApiClient
from blitzsdk.marketdata.instrument_manager import InstrumentManager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg
_client: MarketDataApiClient | None = None


def get_client():
    global _client
    if _client is None:
        _client = MarketDataApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _client


def print_response(data):
    if isinstance(data, dict) or isinstance(data, list):
        _log.info("response=%s", json.dumps(data, indent=2, default=str))
        print(json.dumps(data, indent=2, default=str))
    else:
        _log.info("response=%s", data)
        print(data)


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

    instruments = [i.get("symbol") for i in _conn["Instruments"] if i.get("symbol")]
    instrument_ids = [i["id"] for i in _conn["Instruments"]]
    instrument_id = instrument_ids[0]
    InstrumentManager.load()
    name_symbols = [InstrumentManager._id_cache[iid] for iid in instrument_ids]
    expiry = _conn.get("TestExpiry", "2026-07-07")

    print("--- Market Data API Tests ---")

    def get_instrument_by_id():
        r = client.get_instrument_by_id(instrument_id)
        print_response(r)

    def get_instrument_by_symbol():
        r = client.get_instrument_by_symbol(name_symbols[0])
        print_response(r)

    def get_ltp_by_ids():
        r = client.get_ltp([instrument_id])
        print_response(r)

    def get_ltp_by_names():
        ids = InstrumentManager.resolve_ids(name_symbols)
        r = client.get_ltp(ids)
        print_response(r)

    def get_option_chain():
        r = client.get_option_chain("NIFTY", expiry)
        print_response(r)

    def get_quote_by_ids():
        r = client.get_quote([instrument_id])
        print_response(r)

    def get_quote_by_names():
        ids = InstrumentManager.resolve_ids(name_symbols)
        r = client.get_quote(ids)
        print_response(r)

    def get_historical_data():
        r = client.get_historical_data("RELIANCE", "D")
        print_response(r)

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
    return failed


if __name__ == "__main__":
    sys.exit(run())

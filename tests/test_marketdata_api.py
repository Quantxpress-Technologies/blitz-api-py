import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import MarketDataApiClient
from blitzsdk.marketdata.instrument_manager import InstrumentManager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

_conn = _cfg["Connection"]
_client: MarketDataApiClient | None = None


def _get_client():
    global _client
    if _client is None:
        _client = MarketDataApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    return _client


def _pp(data):
    raw = data.get("response_text", "")
    js = data.get("response_json")
    print(f"  status={data.get('status_code')} raw=({len(raw)} chars)")
    if js is not None:
        print(json.dumps(js, indent=2))


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

    instruments = _conn.get("TestInstruments", ["NSECM|RELIANCE"])
    instrument_id = _conn.get("TestInstrumentId", 110010000002885)
    expiry = _conn.get("TestExpiry", "2026-07-07")

    print("--- Market Data API Tests ---")

    def test_get_instrument_by_id():
        r = client.get_instrument_by_id(instrument_id)
        _pp(r)

    def test_get_instrument_by_symbol():
        r = client.get_instrument_by_symbol(instruments[0])
        _pp(r)

    def test_get_ltp_by_ids():
        r = client.get_ltp([instrument_id])
        _pp(r)

    def test_get_ltp_by_names():
        ids = InstrumentManager.resolve_ids(instruments)
        r = client.get_ltp(ids)
        _pp(r)

    def test_get_option_chain():
        r = client.get_option_chain("NIFTY", expiry)
        _pp(r)

    def test_get_quote_by_ids():
        r = client.get_quote([instrument_id])
        _pp(r)

    def test_get_quote_by_names():
        ids = InstrumentManager.resolve_ids(instruments)
        r = client.get_quote(ids)
        _pp(r)

    def test_get_historical_data():
        r = client.get_historical_data("RELIANCE", "D")
        _pp(r)

    def test_instrument_count():
        InstrumentManager.load()
        print(f"       instruments loaded: {InstrumentManager.count()}")

    # test("GetInstrumentById", test_get_instrument_by_id)
    # test("GetInstrumentBySymbol", test_get_instrument_by_symbol)
    # test("GetLTPByIds", test_get_ltp_by_ids)
    # test("GetLTPByNames", test_get_ltp_by_names)
    # test("GetOptionChain", test_get_option_chain)
    # test("GetQuoteByIds", test_get_quote_by_ids)
    test("GetQuoteByNames", test_get_quote_by_names)
    # test("GetHistoricalData", test_get_historical_data)
    # test("InstrumentCount", test_instrument_count)

    print(f"  PASSED: {passed}   FAILED: {failed}")
    return failed


if __name__ == "__main__":
    sys.exit(run())

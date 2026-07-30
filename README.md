# BlitzConnect Python SDK

[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/blitzsdk/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

The official Python client for communicating with the [BlitzConnect API](https://quantxpress.com/docs/blitz-api).

BlitzConnect is a set of REST-like APIs that expose many capabilities required to build a complete investment and trading platform. Execute orders in real time, manage user portfolio, stream live market data (WebSockets), and more, with the simple HTTP API collection.

[QuantXpress](https://quantxpress.com) (c) 2024. Licensed under the MIT License.

## Documentation

- [BlitzConnect API Reference](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect-api/)
- [Interactive SDK](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect-api/orders/)
- [Market Data SDK](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect-api/ltp/)
- [WebSocket Streaming](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect-api/websocket/)
- [Response structure & Errors](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect/response-structure/)
- [REST API Reference](https://quantxpress.com/docs/blitz-api/api/API_Structure/)

## Installing the client

```bash
pip install blitzsdk
```

Requires Python 3.10+.

## Interactive API usage

```python
import logging
from blitzsdk import InteractiveApiClient
from blitzsdk.interactive.models import OrderRequest

logging.basicConfig(level=logging.DEBUG)

# Create the client (login happens automatically)
client = InteractiveApiClient(app_key="your_api_key", user_id="your_user_id")

# Place an order
try:
    order = OrderRequest(
        instrument_id=110010000014366,
        symbol="NSECM|IDEA",
        quantity=1,
        price=11,
        order_side="BUY",
        order_type="LIMIT",
        product="MIS",
        tif="GFD",
        client_id="your_client_id",
    )
    resp = client.place_order(order)
    blitz_id = resp["response_json"]["data"]["blitzOrderId"]
    logging.info("Order placed. ID is: {}".format(blitz_id))
except Exception as e:
    logging.info("Order placement failed: {}".format(e))

# Modify / Cancel
client.modify_order({
    "BlitzOrderId": 12345,
    "ModifiedOrderQuantity": 2,
    "Price": 10.5,
    "OrderType": "LIMIT",
    "InstrumentId": 110010000014366,
    "Symbol": "NSECM|IDEA",
    "DisclosedQuantity": 0,
    "StopPrice": 0,
    "TIF": "GFD",
})
client.cancel_order(instrument_id=110010000014366, blitz_order_id=12345)

# Fetch orders, positions, trades
client.get_orders()
client.get_open_orders()
client.get_order_by_blitz_id(24091124420000098)
client.get_positions()
client.get_trades()
client.get_statistics()

# Send signals
signals = []
signals.append({
    "ID": "abc",
    "SourceStrategy": "Bull8.DiamondX1",
    "DestinationStrategy": dest,
    "SL": "3000",
    "SourceSID": f"Bull8_SINGLE_{dest}",
    "InstanceRunningMode": "Started",
    "GlobalAction": "Signal",
    "Instruments": [
        {
            "ExchangeSegment": "NSEFO",
            "InstrumentName": instrument_name1,
            "Action": "BUY",
            "Lot": "1",
            "TimeStamp": base_time.strftime("%d-%m-%Y %H:%M:%S"),
            "InfoText": f"{option_type1} Entry Signal {strike1}",
        }
    ],
})
resp = client.send_signals(signals)
```

## Market Data API usage

```python
import logging
from blitzsdk import MarketDataApiClient

logging.basicConfig(level=logging.DEBUG)

# Create the client
md = MarketDataApiClient(app_key="your_api_key", user_id="your_user_id")

# Instrument lookup
md.get_instrument_by_id(110010000002885)
md.get_instrument_by_symbol("NSECM|RELIANCE")

# Live market data
md.get_ltp([110010000002885])
md.get_quote([110010000002885])
md.get_option_chain("NIFTY", "2026-07-30")
md.get_historical_data("RELIANCE", "D")
```

Refer to the [BlitzConnect API Reference](https://quantxpress.com/docs/blitz-api/sdk/blitzconnect-api/) for the complete list of supported methods.

## Interactive WebSocket usage

```python
import logging
from blitzsdk import InteractiveWebSocketClient

logging.basicConfig(level=logging.DEBUG)

# Initialise
ws = InteractiveWebSocketClient(app_key="your_api_key", user_id="your_user_id")

def on_message(data):
    # Callback to receive order and statistics updates.
    mc = data.get("MessageCode", data.get("messageCode", "?"))
    logging.debug("Code: {} Data: {}".format(mc, data))

def on_connect():
    # Callback on successful connect.
    # Subscribe to all order and statistics updates.
    ws.subscribe_action("AllSubscribe")

def on_close(code, msg):
    # On connection close, stop reconnection.
    ws.stop()

# Assign the callbacks.
ws.set_on_message(on_message)
ws.set_on_connect(on_connect)
ws.set_on_close(on_close)

# Start the WebSocket (auto-reconnect on disconnect).
ws.start()
```

## Market Data WebSocket usage

Market data ticks are streamed as **protobuf** (Protocol Buffers) — a compact binary format by Google. The SDK decodes them automatically:

```python
# Inside MarketDataWebSocketClient.on_message():
decoded = base64.b64decode(message)          # decode base64 string
md = marketdata_pb2.MarketDataMessageBase()  # create protobuf object
md.ParseFromString(decoded)                  # parse binary into protobuf
self.on_message_received(md)                 # pass decoded object
```

Use `MessageToJson()` to view the decoded protobuf object as JSON:

```python
import logging
from blitzsdk import MarketDataWebSocketClient
from google.protobuf.json_format import MessageToJson

logging.basicConfig(level=logging.DEBUG)

# Initialise
kws = MarketDataWebSocketClient(app_key="your_api_key", user_id="your_user_id")

def on_ticks(data):
    # data is a decoded protobuf MarketDataMessageBase object
    # Convert to JSON for easy inspection
    logging.debug("Tick: {}".format(MessageToJson(data)))

def on_connect():
    # Subscribe to a list of instrument tokens (NIFTY and RELIANCE here).
    kws.subscribe([110010002000001, 110010000002885])

kws.set_on_message(on_ticks)
kws.set_on_connect(on_connect)

kws.start()
```

## Instrument Manager

Downloads a gzipped JSON file (~140K instruments) from the configured URL and decompresses in memory:

```python
# Inside InstrumentManager.load():
response = requests.get(url, timeout=30)       # download gzipped file
decompressed = gzip.decompress(response.content)  # unzip in memory
data = json.loads(decompressed)                # parse JSON
_cache = {
    f'{item["exchangeSegment"]}|{item["instrumentName"]}': item["instrumentId"]
    for item in data
}
```

Usage:

```python
from blitzsdk.marketdata.instrument_manager import InstrumentManager

InstrumentManager.load()  # downloads + decompresses + caches
instrument_id = InstrumentManager.resolve(symbol="NSECM|RELIANCE")
ids = InstrumentManager.resolve_ids(["NSECM|RELIANCE", "NSECM|NIFTY"])
```

## Run tests

```sh
python tests\test_interactive_api.py
python tests\test_marketdata_api.py
python tests\test_interactive_ws.py
python tests\test_marketdata_ws.py
```

## Changelog

[Check release notes](https://github.com/your-org/blitzsdk/releases)

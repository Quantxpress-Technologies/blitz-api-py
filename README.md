# BlitzConnect Python SDK

Python SDK for the BlitzConnect trading platform — Interactive (order/position management) and Market Data APIs.

## Installation

```bash
pip install -e C:\QuantXpress\QX.BlitzSDK
```

Requires Python 3.10+.

## Configuration

**Option 1: Environment variables**

| Variable | Default |
|---|---|
| `BLITZ_AUTH_URL` | `http://uat.bull8.ai:7443/api_gateway/v1` |
| `BLITZ_API_URL` | `http://uat.bull8.ai:7443/api_interactive/api/v1` |
| `BLITZ_WS_URL` | `ws://uat.bull8.ai:7443/api_interactive/ws` |
| `BLITZ_MD_API_URL` | `http://uat.bull8.ai:7443/md-api` |
| `BLITZ_MD_WS_URL` | `ws://uat.bull8.ai:7443/md-streaming/ws` |

**Option 2: Pass `app_key` and `user_id`** to any client (recommended). Authentication is automatic.

## Interactive API

### Get orders
```python
from blitzsdk import InteractiveApiClient

client = InteractiveApiClient(app_key="your_app_key", user_id="your_user_id")
orders = client.get_orders()
open_orders = client.get_open_orders()
```

### Place an order
```python
from blitzsdk import InteractiveApiClient
from blitzsdk.interactive.models import OrderRequest

client = InteractiveApiClient(app_key="your_app_key", user_id="your_user_id")
order = OrderRequest(
    instrument_id=110010000014366,
    symbol="NSECM|IDEA",
    quantity=1,
    price=11,
    order_side="BUY",
    order_type="LIMIT",
    tif="GFD",
    product="MIS",
    client_id="your_client_id",
)
resp = client.place_order(order)
print(resp["data"]["blitzOrderId"])
```

### Modify / Cancel
```python
client.modify_order({
    "blitzOrderId": 12345,
    "modifiedOrderQuantity": 2,
    "price": 10.5,
    "orderType": "LIMIT",
    "instrumentId": 110010000014366,
    "symbol": "NSECM|IDEA",
    "disclosedQuantity": 0,
    "stopPrice": 0,
    "tif": "GFD",
})

client.cancel_order(instrument_id=110010000014366, blitz_order_id=12345)
```

### Positions, Trades, Signals
```python
positions = client.get_positions()
trades = client.get_trades()
client.send_signals([{...}])
```

### OrderRequest fields

| Parameter | Default |
|---|---|
| `instrument_id` | (required) |
| `symbol` | (required) |
| `quantity` | `1` |
| `price` | `11` |
| `order_side` | `"BUY"` |
| `order_type` | `"LIMIT"` |
| `product` | `"MIS"` |
| `tif` | `"GFD"` |
| `client_id` | `"Prateek123"` |
| `disclosed_quantity` | `0` |
| `stop_price` | `0` |

## Interactive WebSocket

Receive real-time order updates (message code 70000), statistics (50000), strategy stats (80000), and instrument stats (90000).

```python
from blitzsdk import InteractiveWebSocketClient

client = InteractiveWebSocketClient(app_key="your_app_key", user_id="your_user_id")

def on_message(data):
    dd = data.get("decodedData", {})
    print(data)  # full JSON with decodedData

def on_connect():
    print("Connected")
    client.subscribe_action("AllSubscribe")

client.set_on_message(on_message)
client.set_on_connect(on_connect)
client.start()

# Keep running
import time
while True:
    time.sleep(1)
```

**Subscribe to specific categories:**

| Action | Code | Description |
|---|---|---|
| `OrderSubscribe` | 70000 | Order updates |
| `StatisticSubscribe` | 50000 | Account statistics |
| `StrategyStatisticSubscribe` | 80000 | Strategy-level statistics |
| `InstrumentStatisticSubscribe` | 90000 | Instrument-level statistics |
| `AllSubscribe` | all | All of the above |

The server only sends order events when the exchange acknowledges the order (states like "New", "Cancelled", "Complete"). Off-market orders stay in "Pending New" and won't generate WS events.

### WS message format

```json
{
  "messageCode": 70000,
  "entityId": "f684bae4-...",
  "decodedData": {
    "BlitzOrderId": 24091124420000098,
    "OrderStatus": "Cancelled",
    "OrderSide": "Buy",
    "OrderQuantity": 1,
    "OrderPrice": 10,
    "InstrumentName": "IDEA",
    "ExchangeSegment": "NSECM",
    "InstrumentId": 110010000014366,
    "CorrelationOrderId": "order_...",
    "ExchangeOrderId": "",
    "OrderType": "Limit",
    "TimeInForce": "GFD",
    ...
  }
}
```

### WebSocket lifecycle

| Method | Description |
|---|---|
| `start()` | Connect (auto-reconnect on disconnect) |
| `stop()` | Disconnect |
| `subscribe_action(name)` | Subscribe to a message category |
| `unsubscribe_action(name)` | Unsubscribe |

## Market Data API

```python
from blitzsdk import MarketDataApiClient

client = MarketDataApiClient(app_key="your_app_key", user_id="your_user_id")

# Instrument lookup
client.get_instrument_by_id(110010000002885)
client.get_instrument_by_symbol("NSECM|RELIANCE")

# Market data
client.get_ltp([110010000002885])
client.get_quote([110010000002885])
client.get_option_chain("NIFTY", "2026-07-07")
client.get_historical_data("RELIANCE", "D")
```

## Market Data WebSocket

Live streaming of index/equity data via protobuf.

```python
from blitzsdk import MarketDataWebSocketClient

ws = MarketDataWebSocketClient(app_key="your_app_key", user_id="your_user_id")

def on_message(protobuf_msg):
    from google.protobuf.json_format import MessageToJson
    print(MessageToJson(protobuf_msg))

def on_connect():
    ws.subscribe([110010002000001, 110010000002885])  # NIFTY + RELIANCE

ws.set_on_message(on_message)
ws.set_on_connect(on_connect)
ws.start()
```

> **Note:** Subscribe to at least 2 instrument IDs — single-instrument subscribe may cause disconnection.

## Instrument Manager

Resolve symbol names to IDs (downloads ~140K instruments on first use).

```python
from blitzsdk.marketdata.instrument_manager import InstrumentManager

InstrumentManager.load()  # downloads gzipped instrument list
instrument_id = InstrumentManager.resolve(symbol="NSECM|RELIANCE")
ids = InstrumentManager.resolve_ids(["NSECM|RELIANCE", "NSECM|NIFTY"])
count = InstrumentManager.count()  # 140295
```

## Running Tests

```bash
# Market Data API (9 tests)
python tests\test_marketdata_api.py

# Interactive API (9 tests)
python tests\test_interactive_api.py

# Interactive WS listener (stays connected)
python tests\test_interactive_ws.py

# Market Data WS listener (stays connected)
python tests\test_marketdata_ws.py
```

Tests use `tests/test-config.json` for credentials. Update the JSON file to use your own app key and user ID.

## Error Handling

```python
from blitzsdk.common.exceptions import AuthenticationError, RequestError

try:
    client.get_orders()
except AuthenticationError as e:
    print(f"Login failed: {e}")
except RequestError as e:
    print(f"API error {e.status_code}: {e}")
```

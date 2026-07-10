# WebSocket streaming

BlitzConnect provides two WebSocket endpoints — one for **Interactive** events (order updates, positions, statistics) and one for **Market Data** ticks (live prices).

---

## Interactive WebSocket

Receive real-time order, trade, position, and statistics updates.

```
ws://{host}/api_interactive/ws?access_token={token}
```

### Connection

```javascript
var ws = new WebSocket("ws://uat.bull8.ai:7443/api_interactive/ws?access_token=YOUR_TOKEN");
```

### Actions

```json
{"action": "AllSubscribe"}
```

| Action | Event codes subscribed |
|--------|----------------------|
| `OrderSubscribe` | 70000 |
| `OrderUnsubscribe` | Unsubscribes 70000 |
| `StatisticSubscribe` | 50000 |
| `StatisticUnsubscribe` | Unsubscribes 50000 |
| `StrategyStatisticSubscribe` | 80000 |
| `StrategyStatisticUnsubscribe` | Unsubscribes 80000 |
| `InstrumentStatisticSubscribe` | 90000 |
| `InstrumentStatisticUnsubscribe` | Unsubscribes 90000 |
| `AllSubscribe` | Subscribes 50000, 70000, 80000, 90000 |
| `AllUnsubscribe` | Unsubscribes all |

### Message format

Incoming messages are JSON:

```json
{
    "messageCode": 70000,
    "entityId": "entity_001",
    "data": "{\"blitzOrderId\":26082045350000016,\"status\":\"Filled\",...}"
}
```

### Complete message fields

| Field | Type | Description |
|-------|------|-------------|
| `messageCode` | int | 50000=Statistic, 70000=Order, 80000=StrategyStatistic, 90000=InstrumentStatistic |
| `entityId` | string | Entity identifier |
| `data` | string | Raw JSON payload (double-encoded, requires JSON.parse) |
| `decodedData` | object | Parsed `data` JSON (SDK provides this automatically) |

The `data` field contains the full order/position/statistics object with all fields documented in the [Orders](orders.md), [Positions](positions.md), and [Statistics](statistics.md) pages.

---

## Market Data WebSocket

Stream real-time market data ticks as binary Protocol Buffers, automatically decoded by the SDK.

```
ws://{host}/md-streaming/ws?key={token}
```

### Connection

```javascript
var ws = new WebSocket("ws://uat.bull8.ai:7443/md-streaming/ws?key=YOUR_TOKEN");
```

### Subscribe / Unsubscribe

```json
{"action": "subscribe", "instrumentIds": [110010002000001, 110010000002885]}
```

| Action | Payload |
|--------|---------|
| `subscribe` | `{"action": "subscribe", "instrumentIds": [id1, id2, ...]}` |
| `unsubscribe` | `{"action": "unsubscribe", "instrumentIds": [id1, id2, ...]}` |

> Subscribe with **at least 2 instrument IDs**.

### Protobuf schema

```protobuf
message MarketDataMessageBase {
    int32 messageCode = 1;
    int64 ID = 2;
    int32 messageSize = 3;
    oneof payload {
        IndexDataListMessage indexDataList = 8;
        TickDataMessage tickData = 5;
        TouchLineDataMessage touchLineData = 6;
        MarketDepthMessage marketDepth = 7;
        IncrementalUpdateMessage incrementalUpdate = 9;
        TickData tick = 10;
    }
}
```

### TickData fields

| Field | Type | Description |
|-------|------|-------------|
| `InstrumentID` | long | Instrument ID |
| `ExchangeSegment` | int | Exchange segment |
| `ExchangeInstrumentID` | uint | Exchange instrument ID |
| `InstrumentName` | string | Instrument name |
| `TimeStamp` | long | Timestamp (epoch ms) |
| `LTP` | double | Last traded price |
| `LTQ` | int | Last traded quantity |
| `LTT` | long | Last traded time |
| `Flag` | int | Tick flag |

### TouchLineData / MarketDepth fields

| Field | Type | Description |
|-------|------|-------------|
| `InstrumentID` | long | Instrument ID |
| `ExchangeSegment` | int | Exchange segment |
| `ExchangeInstrumentID` | uint | Exchange instrument ID |
| `InstrumentName` | string | Instrument name |
| `TimeStamp` | long | Timestamp |
| `LTP` | double | Last traded price |
| `LTQ` | int | Last traded quantity |
| `LTT` | long | Last traded time |
| `ATP` | double | Average traded price |
| `VTT` | long | Volume today |
| `TBQ` | long | Total buy quantity |
| `TSQ` | long | Total sell quantity |
| `Open` | double | Opening price |
| `High` | double | High price |
| `Low` | double | Low price |
| `Close` | double | Previous close |
| `OI` | long | Open interest |
| `BestBidLevel` | array | Best bid depth levels |
| `BestAskLevel` | array | Best ask depth levels |

### IndexData fields

| Field | Type | Description |
|-------|------|-------------|
| `InstrumentID` | long | Instrument ID |
| `ExchangeSegment` | int | Exchange segment |
| `ExchangeInstrumentID` | uint | Exchange instrument ID |
| `IndexName` | string | Index name |
| `TimeStamp` | long | Timestamp |
| `Last` | double | Last index value |
| `Open` | double | Open value |
| `High` | double | High value |
| `Low` | double | Low value |
| `Close` | double | Close value |
| `YearlyHigh` | double | 52-week high |
| `YearlyLow` | double | 52-week low |
| `NetChangeIndicator` | uint | Net change direction |

### PriceDepthLevel fields

| Field | Type | Description |
|-------|------|-------------|
| `Qty` | int | Quantity at level |
| `Price` | double | Bid/Ask price |
| `Orders` | int | Number of orders |

---

## SDK

=== "Python"

    ```python
    # Interactive WS
    from blitzsdk import InteractiveWebSocketClient

    def on_message(msg):
        print("Code:", msg["messageCode"], "Data:", msg["decodedData"])

    ws = InteractiveWebSocketClient(app_key="YOUR_KEY", user_id="YOUR_USER")
    ws.set_on_message(on_message)
    ws.start()
    ws.subscribe_action("AllSubscribe")
    import time; time.sleep(60)
    ws.stop()

    # Market Data WS
    from blitzsdk import MarketDataWebSocketClient

    def on_tick(md):
        print("Tick:", md)

    ws = MarketDataWebSocketClient(app_key="YOUR_KEY", user_id="YOUR_USER")
    ws.set_on_message(on_tick)
    ws.start()
    ws.subscribe([110010002000001, 110010000002885])
    time.sleep(30)
    ws.stop()
    ```

=== "C#"

    ```csharp
    // Interactive WS
    var iws = new BlitzWebSocketClient(config);
    iws.OnMessage = (msg) => Console.WriteLine($"Code:{msg.MessageCode} Data:{msg.DecodedData}");
    iws.OnConnect = () => Console.WriteLine("Connected!");
    iws.Start();
    await iws.SubscribeActionAsync("AllSubscribe");
    await Task.Delay(60_000);
    iws.Stop();

    // Market Data WS
    var mdws = new BlitzMarketDataWebSocketClient(config);
    mdws.OnMessage = (md) => Console.WriteLine($"Tick: {md}");
    mdws.Start();
    await mdws.SubscribeAsync(new List<long> { 110010002000001, 110010000002885 });
    await Task.Delay(30_000);
    mdws.Stop();
    ```

### Reconnection

Both SDKs auto-reconnect on disconnect. Subscribed actions/instruments are automatically re-sent after each reconnect.

### Known limitations

- **Index data** (NIFTY, BANKNIFTY) streams reliably during market hours
- **Equity and option ticks** may not stream via MD WS on all server configurations — use REST LTP polling as a fallback
- Minimum 2 instrument IDs required for subscribe

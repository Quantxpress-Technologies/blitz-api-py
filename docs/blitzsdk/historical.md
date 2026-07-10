# Historical candle data

Fetch historical OHLC candle data for a specified instrument and time interval.

```
POST /marketfeed/historicalData
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/md-api/marketfeed/historicalData" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Instrument": "NIFTY", "interval": "D"}'
```

### Request fields

| Field | Type | Description |
|-------|------|-------------|
| `Instrument` | string | Instrument symbol (e.g. `NIFTY`, `TCS`) |
| `interval` | string | Candle interval |

### Supported intervals

| Interval | Description |
|----------|-------------|
| `1m` | 1 minute |
| `5m` | 5 minutes |
| `15m` | 15 minutes |
| `1H` | 1 hour |
| `D` | Daily |

### Response

```json
[
    {
        "open": 18490.00,
        "high": 18520.50,
        "low": 18480.10,
        "close": 18510.30,
        "volume": 1250000,
        "oi": 850000,
        "timestamp": "06-07-2026 09:15:00"
    },
    {
        "open": 18510.30,
        "high": 18535.00,
        "low": 18505.00,
        "close": 18530.45,
        "volume": 980000,
        "oi": 850500,
        "timestamp": "06-07-2026 09:16:00"
    }
]
```

### Complete response fields (per candle)

| Field | Type | Description |
|-------|------|-------------|
| `open` | double | Opening price |
| `high` | double | Highest price |
| `low` | double | Lowest price |
| `close` | double | Closing price |
| `volume` | long | Volume traded |
| `oi` | long | Open interest |
| `timestamp` | string | Candle time (`DD-MM-YYYY HH:mm:ss`) |

---

## SDK

=== "Python"

    ```python
    hist = md_client.get_historical_data(instrument="NIFTY", interval="D")
    for candle in hist:
        print(candle["timestamp"], candle["open"], candle["high"], candle["low"], candle["close"], candle["volume"])
    ```

=== "C#"

    ```csharp
    var hist = await mdClient.GetHistoricalDataAsync("NIFTY", "D");
    foreach (var candle in hist)
    {
        Console.WriteLine($"{candle.Timestamp} O:{candle.Open} H:{candle.High} L:{candle.Low} C:{candle.Close} V:{candle.Volume}");
    }
    ```

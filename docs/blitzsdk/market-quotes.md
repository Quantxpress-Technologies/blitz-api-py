# Market quotes

The market data APIs enable you to retrieve LTP, full market quotes, and option chains.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/marketfeed/ltp` | Last traded price for one or more instruments |
| POST | `/marketfeed/quote` | Full market quote with OHLC and bid/ask depth |
| POST | `/marketfeed/optionChain` | Option chain for a symbol and expiry |
| GET | `/v1/api/instruments/{id}` | Instrument details |

---

## LTP

```
POST /marketfeed/ltp
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/md-api/marketfeed/ltp" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"InstrumentIds": [110010002000001, 110010000002885]}'
```

### Request fields

| Field | Type | Description |
|-------|------|-------------|
| `InstrumentIds` | array of long | List of instrument IDs |

### Response

```json
{
    "status": "success",
    "data": {
        "110010002000001": {
            "instrumentId": 110010002000001,
            "ltp": 18532.45
        },
        "110010000002885": {
            "instrumentId": 110010000002885,
            "ltp": 3120.60
        }
    }
}
```

### Response fields (per instrument)

| Field | Type | Description |
|-------|------|-------------|
| `instrumentId` | long | Instrument identifier |
| `ltp` | double | Last traded price |

---

## Market Quote

```
POST /marketfeed/quote
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/md-api/marketfeed/quote" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"InstrumentIds": [110010002000001]}'
```

### Response

```json
{
    "status": "success",
    "data": {
        "110010002000001": {
            "instrumentID": 110010002000001,
            "exchangeSegment": 1,
            "exchangeInstrumentID": 123456,
            "instrumentName": "NIFTY",
            "timestamp": 1770193800000,
            "ltp": 18532.45,
            "ltq": 125,
            "ltt": 1770193800000,
            "atp": 18520.10,
            "vtt": 12500000,
            "tbq": 5000,
            "tsq": 4800,
            "oi": 0,
            "open": 18490.00,
            "high": 18580.50,
            "low": 18475.10,
            "close": 18465.30,
            "bidLevel": [
                {"qty": 150, "price": 18532.00, "orders": 3},
                {"qty": 200, "price": 18531.50, "orders": 2}
            ],
            "askLevel": [
                {"qty": 100, "price": 18532.90, "orders": 4},
                {"qty": 250, "price": 18533.00, "orders": 3}
            ]
        }
    }
}
```

### Complete response fields (per instrument)

| Field | Type | Description |
|-------|------|-------------|
| `instrumentID` | long | Instrument identifier |
| `exchangeSegment` | int | Exchange segment code (1=NSECM, 2=NSEFO, etc.) |
| `exchangeInstrumentID` | int | Exchange-assigned instrument ID |
| `instrumentName` | string | Instrument name |
| `timestamp` | long | Last update timestamp (epoch ms) |
| `ltp` | double | Last traded price |
| `ltq` | int | Last traded quantity |
| `ltt` | long | Last traded time (epoch ms) |
| `atp` | double | Average traded price |
| `vtt` | long | Volume traded today |
| `tbq` | long | Total buy quantity |
| `tsq` | long | Total sell quantity |
| `oi` | long | Open interest |
| `open` | double | Opening price |
| `high` | double | Highest price today |
| `low` | double | Lowest price today |
| `close` | double | Previous closing price |
| `bidLevel` | array | Bid market depth (best 5) |
| `askLevel` | array | Ask market depth (best 5) |

### Market depth level fields

| Field | Type | Description |
|-------|------|-------------|
| `qty` | int | Quantity at this level |
| `price` | double | Bid/Ask price |
| `orders` | int | Number of orders |

---

## Option Chain

```
POST /marketfeed/optionChain
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/md-api/marketfeed/optionChain" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NIFTY", "expiryDate": "2026-07-28"}'
```

### Request fields

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Underlying symbol (e.g. `NIFTY`, `TCS`) |
| `expiryDate` | string | Expiry in `YYYY-MM-DD` format |

### Response

```json
{
    "status": "success",
    "data": {
        "spotPrice": 18532.45,
        "expiryDate": "2026-07-28",
        "atm": 18500.00,
        "chains": [
            {
                "strikePrice": 18500.00,
                "callOption": {
                    "gamma": 0.000045,
                    "vega": 8.25,
                    "theta": -12.50,
                    "delta": 0.52,
                    "oi": 1250000,
                    "oiPercentage": 3.5,
                    "ltp": 245.50,
                    "iv": 14.25,
                    "price": 245.50,
                    "rho": 0.15
                },
                "putOption": {
                    "gamma": 0.000048,
                    "vega": 8.10,
                    "theta": -11.80,
                    "delta": -0.48,
                    "oi": 980000,
                    "oiPercentage": -1.2,
                    "ltp": 180.20,
                    "iv": 15.10,
                    "price": 180.20,
                    "rho": -0.12
                }
            }
        ]
    }
}
```

### Complete response fields

| Field | Type | Description |
|-------|------|-------------|
| `spotPrice` | double | Current LTP of underlying |
| `expiryDate` | string | Expiry date (`YYYY-MM-DD`) |
| `atm` | double | At-The-Money strike price |
| `chains` | array | Array of option chain entries |

### Chain entry fields

| Field | Type | Description |
|-------|------|-------------|
| `strikePrice` | double | Strike price |
| `callOption` | object/null | Call option data (null if not traded) |
| `putOption` | object/null | Put option data |

### Option greeks fields

| Field | Type | Description |
|-------|------|-------------|
| `gamma` | double | Rate of change of delta |
| `vega` | double | Sensitivity to 1% IV change |
| `theta` | double | Time decay per day |
| `delta` | double | Sensitivity to underlying price change |
| `oi` | long | Open interest |
| `oiPercentage` | double | Percentage change in OI |
| `ltp` | double | Last traded price |
| `iv` | double | Implied volatility |
| `price` | double | Last traded or closing price |
| `rho` | double | Sensitivity to interest rate |

---

## Instrument by ID

```
GET /v1/api/instruments/{id}
GET /v1/api/instruments/{exchange}:{symbol}
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": {
        "instrumentId": 110010002000001,
        "exchange": "NSE",
        "symbol": "NIFTY",
        "ticker": "NIFTY 50",
        "exchangeSegment": "NSE",
        "instrumentType": "Index",
        "instrumentName": "NIFTY",
        "exchangeInstrumentId": 123456,
        "marketInstrumentId": 110010002000001,
        "series": null,
        "tickSize": 0.05,
        "isin": null,
        "lotSize": 1,
        "expiryDate": null,
        "strikePrice": null,
        "optionType": null,
        "open": 18490.00,
        "high": 18580.50,
        "low": 18475.10,
        "close": 18465.30,
        "ltp": 18532.45,
        "freezeQty": 0,
        "multiplier": 1,
        "priceBandHigh": 20311.00,
        "priceBandLow": 16620.00,
        "bvp": 0,
        "assetToken": null,
        "underlyingInstrumentId": null
    }
}
```

### Complete response fields

| Field | Type | Description |
|-------|------|-------------|
| `instrumentId` | long | Unique Blitz instrument identifier |
| `exchange` | string | Exchange name (`NSE`, `BSE`, etc.) |
| `symbol` | string | Trading symbol |
| `ticker` | string | Full instrument/company name |
| `exchangeSegment` | string | Segment (`NSECM`, `NSEFO`, etc.) |
| `instrumentType` | string | `Equity`, `Futures`, `Options`, `Index` |
| `instrumentName` | string | Instrument name |
| `exchangeInstrumentId` | int | Exchange-assigned ID |
| `marketInstrumentId` | long | Market-wide instrument ID |
| `series` | string | Series (`EQ`, `XX`, etc.) |
| `tickSize` | double | Minimum price movement |
| `isin` | string | ISIN code |
| `lotSize` | int | Lot size |
| `expiryDate` | string | Expiry date (derivatives) |
| `strikePrice` | double | Strike price (options) |
| `optionType` | string | `CE`, `PE` (options) |
| `open` | double | Opening price |
| `high` | double | Highest price |
| `low` | double | Lowest price |
| `close` | double | Previous close |
| `ltp` | double | Last traded price |
| `freezeQty` | int | Freeze quantity limit |
| `multiplier` | int | Contract multiplier |
| `priceBandHigh` | double | Upper circuit limit |
| `priceBandLow` | double | Lower circuit limit |
| `bvp` | int | Book value per share |
| `assetToken` | string | Asset token reference |
| `underlyingInstrumentId` | long | Underlying instrument ID (options/futures) |

---

## SDK

=== "Python"

    ```python
    from blitzsdk import MarketDataApiClient

    md = MarketDataApiClient(app_key="YOUR_KEY", user_id="YOUR_USER")

    # LTP
    ltp = md.get_ltp([110010002000001])

    # Quote
    quote = md.get_quote([110010002000001])

    # Option chain
    chain = md.get_option_chain("NIFTY", "2026-07-28")

    # Instrument detail
    inst = md.get_instrument_by_id(110010002000001)
    inst = md.get_instrument_by_symbol("NSECM|TCS")
    ```

=== "C#"

    ```csharp
    var config = new BlitzConfig { AppKey = "YOUR_KEY", UserId = "YOUR_USER" };
    var md = new BlitzMarketDataApiClient(config);
    await md.LoginAsync();

    // LTP
    var ltp = await md.GetLtpAsync(new List<long> { 110010002000001 });

    // Quote
    var quote = await md.GetMarketQuoteAsync(new List<long> { 110010002000001 });

    // Option chain
    var chain = await md.GetOptionChainAsync("NIFTY", "2026-07-28");

    // Instrument detail
    var inst = await md.GetInstrumentDetailsAsync(110010002000001);
    ```

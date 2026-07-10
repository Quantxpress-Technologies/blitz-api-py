# Instruments

The instruments API provides a consolidated, import-ready gzipped JSON dump of all tradable instruments.

---

## Download instrument master

```
GET /v1/api/instruments/gz/download
```

```bash
curl "http://uat.bull8.ai:7443/v1/api/instruments/gz/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o instruments.json.gz
```

### Response

The response is a gzipped JSON array. Each entry:

```json
[
    {
        "instrumentId": 110010000011536,
        "exchangeSegment": "NSECM",
        "instrumentName": "TCS",
        "instrumentType": "EQ",
        "lotSize": 1,
        "tickSize": 0.05,
        "expiry": null,
        "strike": null,
        "optionType": null
    },
    {
        "instrumentId": 262090000149108,
        "exchangeSegment": "NSEFO",
        "instrumentName": "TCS28JUL262060CE",
        "instrumentType": "CE",
        "lotSize": 225,
        "tickSize": 0.05,
        "expiry": "2026-07-28",
        "strike": 2060,
        "optionType": "CE"
    }
]
```

### Columns

| Field | Type | Description |
|-------|------|-------------|
| `instrumentId` | long | Blitz internal instrument identifier |
| `exchangeSegment` | string | `NSECM`, `NSEFO`, `BSECM`, `NSE`, etc. |
| `instrumentName` | string | Trading symbol name |
| `instrumentType` | string | `EQ`, `FUT`, `CE`, `PE`, `INDEX` |
| `lotSize` | int | Quantity per lot |
| `tickSize` | double | Minimum price movement |
| `expiry` | string | Expiry date (derivatives) |
| `strike` | double | Strike price (options) |
| `optionType` | string | `CE` or `PE` (options) |

---

## SDK: Instrument Manager

=== "Python"

    ```python
    from blitzsdk import InstrumentManager

    InstrumentManager.load()  # auto-downloads
    # or: InstrumentManager.load("http://uat.bull8.ai:7443/v1/api/instruments/gz/download")

    # Symbol to ID
    tcs_id = InstrumentManager.resolve(symbol="NSECM|TCS")
    print(tcs_id)  # 110010000011536

    # Batch resolve
    ids = InstrumentManager.resolve_ids(["NSECM|TCS", "NSECM|RELIANCE"])

    # Count
    print(InstrumentManager.count())
    ```

=== "C#"

    ```csharp
    var manager = new BlitzInstrumentManager();
    await manager.LoadInstrumentsAsync("http://uat.bull8.ai:7443/v1/api/instruments/gz/download");

    long tcsId = manager.GetInstrumentId("NSECM", "TCS");
    Console.WriteLine(tcsId);  // 110010000011536

    string symbol = manager.GetInstrumentKey(110010000011536);
    Console.WriteLine(symbol);  // NSECM|TCS

    bool found = manager.TryGetInstrumentId("NSECM|TCS", out long id);

    Console.WriteLine($"Total: {manager.Count}");
    ```

### Symbol format

| Exchange | Segment | Format | Example |
|----------|---------|--------|---------|
| NSE Cash | `NSECM` | `NSECM\|SYMBOL` | `NSECM\|TCS` |
| NSE F&O | `NSEFO` | `NSEFO\|SYMBOL` | `NSEFO\|TCS28JUL262060CE` |
| BSE Cash | `BSECM` | `BSECM\|SYMBOL` | `BSECM\|TCS` |
| NSE Index | `NSE` | `NSE\|SYMBOL` | `NSE\|NIFTY` |

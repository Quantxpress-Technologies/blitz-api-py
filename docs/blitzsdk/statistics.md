# Statistics

Retrieve strategy-level trading statistics and performance metrics.

```
GET /strategy/statistics
```

```bash
curl "http://uat.bull8.ai:7443/api_interactive/api/v1/strategy/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": [
        {
            "entityId": "entity_001",
            "strategyId": "strat_001",
            "strategyName": "Manual Trading",
            "strategyInstanceId": "inst_001",
            "strategyInstanceName": "NSECM|TCS",
            "exchangeClientId": "Algo123",
            "instrumentId": 110010000011536,
            "ivName": "TCS",
            "exchangeSegment": "NSECM",
            "instrumentName": "TCS",
            "nonAckBuyQuantity": 0,
            "nonAckSellQuantity": 0,
            "openBuyQuantity": 0,
            "openSellQuantity": 225,
            "shortPosition": 225,
            "longPosition": 0,
            "netPosition": -225,
            "netPositionInLot": -1,
            "orderCount": 2,
            "tradeCount": 2,
            "previousNetPosition": 0,
            "tradeBuyValue": 0.0,
            "tradeSellValue": 21498.75,
            "tradeNetValue": -21498.75,
            "avgBuy": 0.0,
            "avgSell": 95.55,
            "avgNet": 95.55,
            "opBuyPrice": 0.0,
            "opSellPrice": 95.55,
            "exposure": 21498.75,
            "unrealized": 850.00,
            "realized": 0.0,
            "lastTradedPrice": 91.75,
            "openPositionTradeValue": 20643.75,
            "turnoverValue": 21498.75,
            "turnoverValueOptions": 21498.75
        }
    ]
}
```

### Complete response fields (per strategy entry)

| Field | Type | Description |
|-------|------|-------------|
| `entityId` | string | Entity identifier |
| `strategyId` | string | Strategy identifier |
| `strategyName` | string | Strategy name |
| `strategyInstanceId` | string | Strategy instance ID |
| `strategyInstanceName` | string | Strategy instance name |
| `exchangeClientId` | string | Exchange client ID |
| `instrumentId` | long | Blitz internal instrument ID |
| `ivName` | string | IV name |
| `exchangeSegment` | string | Exchange segment |
| `instrumentName` | string | Instrument trading name |
| `nonAckBuyQuantity` | int | Non-acknowledged buy quantity |
| `nonAckSellQuantity` | int | Non-acknowledged sell quantity |
| `openBuyQuantity` | int | Open buy quantity |
| `openSellQuantity` | int | Open sell quantity |
| `shortPosition` | int | Short position |
| `longPosition` | int | Long position |
| `netPosition` | int | Net position |
| `netPositionInLot` | int | Net position in lots |
| `orderCount` | int | Total order count |
| `tradeCount` | int | Total trade count |
| `previousNetPosition` | int | Previous session net position |
| `tradeBuyValue` | double | Buy trade value |
| `tradeSellValue` | double | Sell trade value |
| `tradeNetValue` | double | Net trade value |
| `avgBuy` | double | Average buy price |
| `avgSell` | double | Average sell price |
| `avgNet` | double | Average net price |
| `opBuyPrice` | double | Open buy price |
| `opSellPrice` | double | Open sell price |
| `exposure` | double | Total exposure |
| `unrealized` | double | Unrealized P&L |
| `realized` | double | Realized P&L |
| `lastTradedPrice` | double | Current market price |
| `openPositionTradeValue` | double | Open position trade value |
| `turnoverValue` | double | Total turnover |
| `turnoverValueOptions` | double | Options turnover |

---

## SDK

=== "Python"

    ```python
    stats = client.get_statistics()
    for s in stats.get("data", []):
        print(s["strategyName"], s["instrumentName"], s["netPosition"], s["unrealized"])
    ```

=== "C#"

    ```csharp
    var stats = await client.GetStatisticsAsync();
    foreach (var s in stats.Data)
    {
        Console.WriteLine($"{s.StrategyName} {s.InstrumentName} Net:{s.NetPosition} P&L:{s.Unrealized}");
    }
    ```

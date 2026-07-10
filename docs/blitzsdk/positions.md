# Positions

Retrieve consolidated position details across all executed trades and active holdings.

```
GET /positions
```

```bash
curl "http://uat.bull8.ai:7443/api_interactive/api/v1/positions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": {
        "Algo123": [
            {
                "entityId": "entity_001",
                "clientId": "Algo123",
                "rmsEntityCode": "RMS001",
                "instrumentId": 262090000149108,
                "exchangeSegment": "NSEFO",
                "instrumentName": "TCS28JUL262060CE",
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
}
```

### Complete response fields (per position)

| Field | Type | Description |
|-------|------|-------------|
| `entityId` | string | Entity identifier |
| `clientId` | string | Client identifier |
| `rmsEntityCode` | string | RMS entity code |
| `instrumentId` | long | Blitz internal instrument ID |
| `exchangeSegment` | string | Exchange segment (`NSECM`, `NSEFO`, etc.) |
| `instrumentName` | string | Instrument trading name |
| `nonAckBuyQuantity` | int | Non-acknowledged buy quantity |
| `nonAckSellQuantity` | int | Non-acknowledged sell quantity |
| `openBuyQuantity` | int | Total open buy quantity |
| `openSellQuantity` | int | Total open sell quantity |
| `shortPosition` | int | Short position quantity |
| `longPosition` | int | Long position quantity |
| `netPosition` | int | Net position (positive=long, negative=short) |
| `netPositionInLot` | int | Net position in lots |
| `orderCount` | int | Total orders for this position |
| `tradeCount` | int | Total trades executed |
| `previousNetPosition` | int | Previous session's net position |
| `tradeBuyValue` | double | Total buy trade value |
| `tradeSellValue` | double | Total sell trade value |
| `tradeNetValue` | double | Net trade value (sell - buy) |
| `avgBuy` | double | Average buy price |
| `avgSell` | double | Average sell price |
| `avgNet` | double | Average net price |
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
    positions = client.get_positions()
    for client_id, pos_list in positions.get("data", {}).items():
        for pos in pos_list:
            print(pos["instrumentName"], pos["netPosition"], pos["unrealized"])
    ```

=== "C#"

    ```csharp
    var positions = await client.GetPositionsAsync();
    foreach (var pos in positions.Data.Positions)
    {
        Console.WriteLine($"{pos.InstrumentName} Net:{pos.NetPosition} P&L:{pos.Unrealized}");
    }
    ```

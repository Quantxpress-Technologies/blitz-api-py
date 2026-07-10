# Trades

Returns trade-level execution information for completed or partially completed orders.

```
GET /trades
```

```bash
curl "http://uat.bull8.ai:7443/api_interactive/api/v1/trades" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": [
        {
            "blitzOrderId": 26082045350000016,
            "exchangeOrderId": "3000000001887410",
            "executionId": "trade_000001",
            "instrumentId": 110010000011536,
            "exchangeSegment": "NSECM",
            "exchangeInstrumentId": 123456,
            "instrumentName": "TCS",
            "instrumentType": 1,
            "clientId": "Algo123",
            "account": "DA0017",
            "orderType": "Limit",
            "orderSide": "Sell",
            "status": "Filled",
            "orderQuantity": 225,
            "orderPrice": 4100.00,
            "lastTradedQuantity": 225,
            "lastTradedPrice": 4098.50,
            "cumulativeQuantity": 225,
            "leavesQuantity": 0,
            "averageTradedPrice": 4098.50,
            "averageTradedValue": 922162.50,
            "tif": "GFD",
            "orderGeneratedDateTime": 1770193800000,
            "lastRequestDateTime": 1770193805000,
            "exchangeTransactTime": 1770193805000,
            "orderModificationCount": 0,
            "orderTradeCount": 1,
            "correlationOrderId": "st_fce5e303acde4f738",
            "orderTag": "NormalOrder",
            "executionType": "Fill",
            "rejectType": "None",
            "orderStopPrice": 0.00,
            "orderTriggerPrice": 0.00,
            "orderDisclosedQuantity": 0,
            "minimumQuantity": 0,
            "orderExpiryDate": 0,
            "isFictiveOrder": false,
            "isOrderCompleted": true,
            "entityId": "entity_001",
            "strategyId": null,
            "strategyInstanceId": null,
            "strategyName": "Manual Trading",
            "strategyInstanceName": "NSECM|TCS",
            "strategyTag": "General",
            "ivObjectName": null,
            "ctclId": null,
            "algoId": null,
            "algoCategoryId": null,
            "clearingFirmId": null,
            "panId": null,
            "userText": null,
            "sequenceNumber": 1
        }
    ]
}
```

### Complete response fields (per trade)

| Field | Type | Description |
|-------|------|-------------|
| `blitzOrderId` | long | Blitz order ID |
| `exchangeOrderId` | string | Exchange-assigned order ID |
| `executionId` | string | Exchange execution/trade ID |
| `instrumentId` | long | Blitz internal instrument ID |
| `exchangeSegment` | string | Exchange segment |
| `exchangeInstrumentId` | long | Exchange instrument ID |
| `instrumentName` | string | Instrument trading name |
| `instrumentType` | int | 1=Equity, 2=F&O |
| `clientId` | string | Client identifier |
| `account` | string | Account code |
| `orderType` | string | `Limit`, `Market`, `SL`, `SL-M` |
| `orderSide` | string | `Buy` or `Sell` |
| `status` | string | Order status at time of trade |
| `orderQuantity` | int | Total order quantity |
| `orderPrice` | double | Order limit price |
| `lastTradedQuantity` | int | Executed quantity for this trade |
| `lastTradedPrice` | double | Execution price |
| `cumulativeQuantity` | int | Total filled quantity |
| `leavesQuantity` | int | Remaining quantity |
| `averageTradedPrice` | double | Average fill price |
| `averageTradedValue` | double | Total traded value |
| `tif` | string | Time in force |
| `orderGeneratedDateTime` | long | Order timestamp (epoch ms) |
| `lastRequestDateTime` | long | Last request timestamp (epoch ms) |
| `exchangeTransactTime` | long | Exchange transaction time (epoch ms) |
| `orderModificationCount` | int | Modification count |
| `orderTradeCount` | int | Number of trades for this order |
| `correlationOrderId` | string | Client correlation ID |
| `orderTag` | string | Order tag |
| `executionType` | string | `Fill`, `PartialFill`, etc. |
| `rejectType` | string | Rejection category |
| `orderStopPrice` | double | Stop loss price |
| `orderTriggerPrice` | double | Trigger price |
| `orderDisclosedQuantity` | int | Disclosed quantity |
| `minimumQuantity` | int | Minimum quantity |
| `orderExpiryDate` | long | Expiry date (epoch ms) |
| `isFictiveOrder` | bool | Is simulated |
| `isOrderCompleted` | bool | Order lifecycle complete |
| `entityId` | string | Entity identifier |
| `strategyId` | string | Strategy ID |
| `strategyInstanceId` | string | Strategy instance ID |
| `strategyName` | string | Strategy name |
| `strategyInstanceName` | string | Strategy instance name |
| `strategyTag` | string | Strategy tag |
| `ivObjectName` | string | IV object name |
| `ctclId` | string | CTCL ID |
| `algoId` | string | Algorithm ID |
| `algoCategoryId` | string | Algorithm category ID |
| `clearingFirmId` | string | Clearing firm ID |
| `panId` | string | PAN ID |
| `userText` | string | User remarks |
| `sequenceNumber` | long | Sequence number |

---

## SDK

=== "Python"

    ```python
    trades = client.get_trades()
    for t in trades.get("data", []):
        print(t["instrumentName"], t["orderSide"], t["lastTradedQuantity"], t["lastTradedPrice"])
    ```

=== "C#"

    ```csharp
    var trades = await client.GetTradesAsync();
    foreach (var t in trades.Data.Trades)
    {
        Console.WriteLine($"{t.InstrumentName} {t.OrderSide} Qty:{t.LastTradedQuantity} @ {t.LastTradedPrice}");
    }
    ```

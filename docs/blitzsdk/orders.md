# Orders

The order APIs let you place orders of different types, modify and cancel pending orders, and retrieve the daily order book.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/orders/placeOrder` | Place an order |
| PUT | `/orders/modifyOrder` | Modify an open or pending order |
| DELETE | `/orders/cancelOrder` | Cancel an open or pending order |
| GET | `/orders` | Retrieve all orders for the day |
| GET | `/orders/openOrders` | Retrieve open orders |
| GET | `/orders/{blitzOrderId}` | Retrieve a specific order by Blitz order ID |

---

## Glossary of constants

### Order types

| Value | Description |
|-------|-------------|
| `LIMIT` | Limit order |
| `MARKET` | Market order |
| `SL` | Stop-loss limit order |
| `SL-M` | Stop-loss market order |

### Product types

| Value | Description |
|-------|-------------|
| `MIS` | Margin Intraday Squareoff |
| `CNC` | Cash & Carry (equity delivery) |
| `NRML` | Normal (F&O) |

### Order sides

| Value | Description |
|-------|-------------|
| `BUY` | Buy |
| `SELL` | Sell |

### Time in force

| Value | Description |
|-------|-------------|
| `GFD` | Good for the day |
| `GTD` | Good till date |
| `IOC` | Immediate or cancel |
| `DAY` | Day order |

### Order statuses

| Status | Description |
|--------|-------------|
| `PendingNew` | Order received, pending validation |
| `New` | Order placed and open at exchange |
| `Filled` | Order fully executed |
| `PartiallyFilled` | Order partially filled, remaining open |
| `Cancelled` | Order cancelled |
| `PendingCancel` | Cancel request sent, awaiting confirmation |
| `Rejected` | Order rejected by exchange or RMS |
| `Expired` | Order expired (GTD/IOC) |
| `TriggerPending` | SL/SL-M order waiting for trigger |

### Execution types

| Value | Description |
|-------|-------------|
| `None` | No execution event |
| `New` | New order acknowledged |
| `Fill` | Order filled |
| `PartialFill` | Order partially filled |
| `Canceled` | Order cancelled |
| `Rejected` | Order rejected |
| `Modify` | Order modified |

---

## Placing orders

```
POST /orders/placeOrder
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/api_interactive/api/v1/orders/placeOrder" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "correlationOrderId": "order_1712345678000",
    "instrumentId": 110010000011536,
    "symbol": "NSECM|TCS",
    "quantity": 225,
    "price": 4100,
    "orderSide": "SELL",
    "orderType": "LIMIT",
    "product": "MIS",
    "tif": "GFD",
    "clientId": "Algo123",
    "disclosedQuantity": 0,
    "stopPrice": 0,
    "tiF_GTD_Date": "2025-10-10"
}'
```

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlationOrderId` | string | Yes | Unique client-generated order identifier |
| `instrumentId` | long | Yes | Blitz instrument ID |
| `symbol` | string | Yes | Exchange segment \| instrument name (e.g. `NSECM|TCS`) |
| `quantity` | int | Yes | Order quantity |
| `price` | double | Yes | Limit price (0 for MARKET) |
| `orderSide` | string | Yes | `BUY` or `SELL` |
| `orderType` | string | Yes | `LIMIT`, `MARKET`, `SL`, `SL-M` |
| `product` | string | Yes | `MIS`, `CNC`, `NRML` |
| `tif` | string | Yes | `GFD`, `GTD`, `IOC`, `DAY` |
| `clientId` | string | Yes | Trading client ID |
| `disclosedQuantity` | int | No | Quantity to disclose (default 0) |
| `stopPrice` | double | No | Trigger price for SL orders (default 0) |
| `tiF_GTD_Date` | string | No | GTD expiry date (`YYYY-MM-DD`, required if `tif=GTD`) |

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": {
        "blitzOrderId": 26082045350000016,
        "correlationOrderId": "st_fce5e303acde4f738"
    }
}
```

### Response fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"success"` or `"error"` |
| `message` | string | Response message |
| `data` | object | Container |
| `data.blitzOrderId` | long | System-assigned unique order ID |
| `data.correlationOrderId` | string | Client-provided correlation ID |

---

## Modifying orders

```
PUT /orders/modifyOrder
```

### Request fields

| Field | Type | Description |
|-------|------|-------------|
| `blitzOrderId` | long | Order ID to modify |
| `quantity` | int | Updated quantity |
| `price` | double | Updated price |
| `orderType` | string | `LIMIT`, `MARKET`, etc. |
| `symbol` | string | Exchange segment \| symbol |
| `disclosedQuantity` | int | Updated disclosed quantity |
| `stopPrice` | double | Updated trigger price |
| `tif` | string | Updated time in force |

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": "successfully send modify order request to blitz server"
}
```

---

## Cancelling orders

```
DELETE /orders/cancelOrder?instrumentId={id}&blitzOrderId={id}
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": "successfully send cancel order request to blitz server"
}
```

---

## Retrieving orders

```
GET /orders
GET /orders/openOrders
GET /orders/{blitzOrderId}
```

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": [
        {
            "blitzOrderId": 26082045350000016,
            "correlationOrderId": "st_fce5e303acde4f738",
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
            "orderStopPrice": 0.00,
            "orderTriggerPrice": 0.00,
            "cumulativeQuantity": 225,
            "leavesQuantity": 0,
            "lastTradedQuantity": 225,
            "lastTradedPrice": 4098.50,
            "averageTradedPrice": 4098.50,
            "averageTradedValue": 922162.50,
            "tif": "GFD",
            "orderDisclosedQuantity": 0,
            "minimumQuantity": 0,
            "orderGeneratedDateTime": 1770193800000,
            "lastRequestDateTime": 1770193805000,
            "exchangeTransactTime": 1770193805000,
            "exchangeOrderId": "3000000001887410",
            "executionId": null,
            "orderModificationCount": 0,
            "orderTradeCount": 1,
            "orderTag": "NormalOrder",
            "executionType": "Fill",
            "rejectType": "None",
            "rejectTypeReason": null,
            "isFictiveOrder": false,
            "isOrderCompleted": true,
            "strategyId": null,
            "strategyInstanceId": null,
            "strategyName": "Manual Trading",
            "strategyInstanceName": "NSECM|TCS",
            "strategyTag": "General",
            "entityId": "entity_001",
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

### Complete response fields (per order)

| Field | Type | Description |
|-------|------|-------------|
| `blitzOrderId` | long | System-assigned unique order ID |
| `correlationOrderId` | string | Client-provided correlation ID |
| `instrumentId` | long | Blitz internal instrument ID |
| `exchangeSegment` | string | Exchange segment (`NSECM`, `NSEFO`, etc.) |
| `exchangeInstrumentId` | long | Exchange-assigned instrument ID |
| `instrumentName` | string | Instrument trading name |
| `instrumentType` | int | 1=Equity, 2=F&O |
| `clientId` | string | Client identifier |
| `account` | string | Account code |
| `orderType` | string | `Limit`, `Market`, `SL`, `SL-M` |
| `orderSide` | string | `Buy` or `Sell` |
| `status` | string | `PendingNew`, `New`, `Filled`, `PartiallyFilled`, `Cancelled`, `Rejected`, `Expired`, `TriggerPending` |
| `orderQuantity` | int | Total requested quantity |
| `orderPrice` | double | Limit price (0 for Market) |
| `orderStopPrice` | double | Stop loss trigger price |
| `orderTriggerPrice` | double | Conditional trigger price |
| `cumulativeQuantity` | int | Total filled quantity |
| `leavesQuantity` | int | Remaining quantity to fill |
| `lastTradedQuantity` | int | Quantity of most recent fill |
| `lastTradedPrice` | double | Price of most recent fill |
| `averageTradedPrice` | double | Average price of all fills |
| `averageTradedValue` | double | Total traded value |
| `tif` | string | `GFD`, `GTD`, `DAY`, `IOC` |
| `orderDisclosedQuantity` | int | Quantity disclosed to market |
| `minimumQuantity` | int | Minimum quantity to execute |
| `orderGeneratedDateTime` | long | Order creation timestamp (epoch ms) |
| `lastRequestDateTime` | long | Last modification timestamp (epoch ms) |
| `exchangeTransactTime` | long | Exchange transaction timestamp (epoch ms) |
| `exchangeOrderId` | string | Exchange-assigned order ID |
| `executionId` | string | Exchange execution/trade ID |
| `orderModificationCount` | int | Number of times modified |
| `orderTradeCount` | int | Number of fills (trades) |
| `orderTag` | string | `NormalOrder` or similar |
| `executionType` | string | `None`, `New`, `Fill`, `PartialFill`, `Canceled`, `Rejected`, `Modify` |
| `rejectType` | string | `None` or rejection category |
| `rejectTypeReason` | string | Reason for rejection |
| `isFictiveOrder` | bool | Whether simulated |
| `isOrderCompleted` | bool | Whether lifecycle complete |
| `strategyId` | string | Strategy ID |
| `strategyInstanceId` | string | Strategy instance ID |
| `strategyName` | string | Strategy name |
| `strategyInstanceName` | string | Strategy instance name |
| `strategyTag` | string | Strategy category tag |
| `entityId` | string | Entity identifier |
| `ivObjectName` | string | IV object name |
| `ctclId` | string | CTCL ID |
| `algoId` | string | Algorithm ID |
| `algoCategoryId` | string | Algorithm category ID |
| `clearingFirmId` | string | Clearing firm ID |
| `panId` | string | PAN associated with account |
| `userText` | string | Custom user remarks |
| `sequenceNumber` | long | Event sequence number |

---

## SDK

=== "Python"

    ```python
    from blitzsdk import InteractiveApiClient
    from blitzsdk.interactive.models import OrderRequest

    client = InteractiveApiClient(app_key="YOUR_KEY", user_id="YOUR_USER")

    # Place order
    order = OrderRequest(
        instrument_id=110010000011536,
        symbol="NSECM|TCS",
        quantity=225,
        price=4100,
        order_side="SELL",
        order_type="LIMIT",
        product="MIS",
        tif="GFD",
        client_id="Algo123",
    )
    resp = client.place_order(order)
    print(resp)

    # Get orders
    orders = client.get_orders()
    open_orders = client.get_open_orders()
    order = client.get_order_by_blitz_id(26082045350000016)

    # Cancel
    resp = client.cancel_order(
        instrument_id=110010000011536,
        blitz_order_id=26082045350000016,
    )
    ```

=== "C#"

    ```csharp
    var config = new BlitzConfig { AppKey = "YOUR_KEY", UserId = "YOUR_USER" };
    var client = new BlitzInteractiveApiClient(config);
    await client.LoginAsync();

    // Place order
    var order = new PlaceOrderRequest
    {
        InstrumentId = 110010000011536,
        Symbol = "NSECM|TCS",
        Quantity = 225,
        Price = 4100,
        OrderSide = "SELL",
        OrderType = "LIMIT",
        Product = "MIS",
        TimeInForce = "GFD",
        ClientId = "Algo123",
    };
    var resp = await client.PlaceOrderAsync(order);

    // Get orders
    var orders = await client.GetOrdersAsync();
    var openOrders = await client.GetOpenOrdersAsync();

    // Cancel
    var cancel = new CancelOrderRequest
    {
        InstrumentId = 110010000011536,
        BlitzOrderId = 26082045350000016,
    };
    await client.CancelOrderAsync(cancel);
    ```

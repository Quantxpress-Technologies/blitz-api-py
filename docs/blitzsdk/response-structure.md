# Response structure

All responses from the API are JSON with the content-type `application/json` unless explicitly stated otherwise.

## Successful request

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "success",
    "data": {}
}
```

A successful `200 OK` response always has a JSON response body with a `status` key with the value `"success"`. The `data` key contains the full response payload.

## Failed request

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "status": "error",
    "message": "Error description",
    "error_type": "InputException"
}
```

A failure response is preceded by the corresponding `40x` or `50x` HTTP header. The `status` key contains `"error"`. The `message` key contains a textual description and `error_type` contains the exception name.

## Data types

| JSON type | Notes |
|-----------|-------|
| `string` | Text values |
| `int` | Integer values (instrument IDs, quantities) |
| `float` | Decimal values (prices, LTP) |
| `bool` | Boolean flags |

Timestamp strings are represented in the format `yyyy-mm-dd hh:mm:ss` in Indian timezone (IST, UTC+5:30).

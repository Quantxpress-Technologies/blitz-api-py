# Authentication

Call the login endpoint with your `app_key` and `user_id` to receive an `access_token`. Include this token as a Bearer header in all subsequent API requests.

---

## Login

```
POST /api/app_login
```

### Request

```bash
curl -X POST "http://uat.bull8.ai:7443/api_gateway/v1/api/app_login" \
  -H "Content-Type: application/json" \
  -d '{"appKey": "YOUR_APP_KEY", "userId": "YOUR_USER_ID"}'
```

### Request fields

| Field | Type | Description |
|-------|------|-------------|
| `appKey` | string | Application key provided by the platform |
| `userId` | string | User identifier |

### Response

```json
{
    "status": "success",
    "message": "request processed successfully",
    "data": {
        "accessToken": "eyJhbGciOiJIUzI1NiIs..."
    }
}
```

### Complete response fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"success"` or `"error"` |
| `message` | string | Response message |
| `data` | object | Container |
| `data.accessToken` | string | JWT access token |

The `accessToken` is a JWT. Include it in all API requests as:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## SDK usage

=== "Python"

    ```python
    from blitzsdk import InteractiveApiClient

    # Login happens automatically on first API call
    client = InteractiveApiClient(app_key="YOUR_KEY", user_id="YOUR_USER")
    ```

=== "C#"

    ```csharp
    var config = new BlitzConfig { AppKey = "YOUR_KEY", UserId = "YOUR_USER" };
    var client = new BlitzInteractiveApiClient(config);
    await client.LoginAsync();  // Explicit login
    ```

---

## Token expiry

Tokens are valid for a limited duration. When a `401` or `403` response is received, the SDK automatically re-authenticates and retries the request.

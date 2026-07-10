# BlitzConnect

BlitzConnect is a set of REST-like HTTP APIs that expose capabilities required to build algorithmic trading and market data applications. It lets you place and manage orders in real time (equities, futures, options), stream live market data over WebSocket, manage portfolios, and more.

All inputs are JSON-encoded parameters and responses are JSON. Standard HTTP codes are used to indicate success and error states with accompanying JSON data.

An `app_key` + `user_id` pair is issued by the platform. Authentication is done via a simple login endpoint that returns an `access_token` used as a Bearer token in subsequent requests.

---

## Base URLs

| Environment | Auth | Interactive API | Market Data | Instruments |
|-------------|------|----------------|-------------|-------------|
| Bull8 (default) | `http://uat.bull8.ai:7443/api_gateway/v1` | `http://uat.bull8.ai:7443/api_interactive/api/v1` | `http://uat.bull8.ai:7443/md-api` | `http://uat.bull8.ai:7443/v1/api` |
| QuantXpress | `http://uat.quantxpress.com/api_gateway/v1` | `http://uat.quantxpress.com/interactive/v1/api/v1` | `http://uat.quantxpress.com/md-api` | `http://uat.quantxpress.com/v1` |

---

## Getting Started

To use BlitzConnect APIs, you'll need:

1. **Account credentials** — `app_key` and `user_id` from the Blitz portal.
2. **Authentication** — Call the login endpoint to get an `access_token`. See [Authentication](authentication.md).
3. **Pick your SDK** — Use one of our [client libraries](sdks.md) for Python or C#.
4. **Start building** — Place orders, stream ticks, build your strategy.

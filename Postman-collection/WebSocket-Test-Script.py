#!/usr/bin/env python3
"""
BlitzTrader WebSocket smoke test.

Postman cannot do this job. A Postman v2.1 collection cannot hold WebSocket
requests next to HTTP requests, and Postman cannot export WebSocket requests
in v2.1 JSON at all - any WebSocket entry in a collection file imports back as
a plain HTTP GET. This script covers both BlitzTrader sockets instead.

    Interactive   <scheme>://<host>/api_interactive/ws?access_token=<JWT>
                  order, trade, position and statistics events as plain JSON.

    Market Data   <scheme>://<host>/md-streaming/ws?key=<JWT>
                  live ticks as base64-encoded protobuf. Note the parameter
                  name is key=, not access_token=.

Usage
-----
    python WebSocket-Test-Script.py --collection BlitzConnect.postman_collection.json
    python WebSocket-Test-Script.py --mode md --instrument-id 110010000002885 --seconds 20
    python WebSocket-Test-Script.py --dry-run          # print config, hit nothing

Reads appKey, userId, gatewayBaseUrl, wsHost, wsScheme and instrumentId straight
out of the Postman collection, so the collection stays the single source of
truth. Any value can be overridden on the command line or via the environment.

Requires: pip install requests websockets
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import ssl
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests")

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, InvalidStatus
except ImportError:
    sys.exit("Missing dependency. Run: pip install websockets")


HEARTBEAT_SECONDS = 30
MAX_FRAME_BYTES = 16 * 1024 * 1024

INTERACTIVE_CODES = {
    50000: "instrument statistic",
    70000: "order",
    80000: "strategy statistic",
    90000: "instrument statistic",
}

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def log(tag: str, message: str) -> None:
    print(f"[{tag}] {message}", flush=True)


def mask(token: str, keep: int = 6) -> str:
    if not token:
        return "<empty>"
    if len(token) <= keep:
        return "*" * len(token)
    return token[:keep] + f"...<{len(token)} chars>"


def safe_url(url: str, token: str) -> str:
    """The JWT rides in the query string, so never log it in full - these logs
    end up in bug reports."""
    return url.replace(token, mask(token)) if token else url


def read_collection_vars(path: str) -> dict[str, str]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    raw = {
        str(v.get("key")): str(v.get("value") or "")
        for v in data.get("variable", [])
    }
    # Base URLs are stored as templates like "{{BaseUrl}}/api_gateway/v1" so a
    # consumer can retarget the environment by editing one variable. Postman
    # expands those itself; this script has to do it, or it would try to dial a
    # literal "{{BaseUrl}}". Resolve repeatedly so derived-of-derived works.
    for _ in range(10):
        expanded = {
            k: re.sub(r"\{\{(\w+)\}\}", lambda m: raw.get(m.group(1), m.group(0)), v)
            for k, v in raw.items()
        }
        if expanded == raw:
            break
        raw = expanded
    return raw


def pick(
    cli: str | None, env: str, collection: dict[str, str], key: str, default: str
) -> str:
    if cli:
        return cli
    if os.getenv(env):
        return os.environ[env]
    if collection.get(key):
        return collection[key]
    return default


def load_sdk_pb2(explicit: str | None):
    """Reuse the SDK's generated protobuf module, so the wire format cannot
    drift from what the SDK itself parses."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.getenv("BLITZ_SDK_PATH"):
        candidates.append(Path(os.environ["BLITZ_SDK_PATH"]))
    here = Path(__file__).resolve().parent
    candidates += [here / "blitz-api-py", here.parent / "blitz-api-py"]

    for root in candidates:
        if (root / "blitzsdk" / "proto" / "marketdata_pb2.py").is_file():
            sys.path.insert(0, str(root))
            break
    else:
        return None, None

    try:
        from google.protobuf.descriptor import FieldDescriptor

        from blitzsdk.proto import marketdata_pb2

        return marketdata_pb2, FieldDescriptor
    except Exception as exc:  # pragma: no cover - depends on local install
        log("md", f"could not load the SDK protobuf module: {exc}")
        return None, None


def protobuf_to_dict(msg, FieldDescriptor) -> dict[str, Any]:
    """ListFields gives us only the fields the server actually populated, so
    the output stays readable instead of dumping every zero."""

    def scalar(fd, value):
        if fd.type == FieldDescriptor.TYPE_ENUM:
            return fd.enum_type.values_by_number[value].name
        if isinstance(value, float):
            return round(value, 6)
        return value

    def node(message) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for fd, value in message.ListFields():
            if fd.type == FieldDescriptor.TYPE_MESSAGE:
                if fd.label == FieldDescriptor.LABEL_REPEATED:
                    out[fd.name] = [node(v) for v in value]
                else:
                    out[fd.name] = node(value)
            elif fd.label == FieldDescriptor.LABEL_REPEATED:
                out[fd.name] = [scalar(fd, v) for v in value]
            else:
                out[fd.name] = scalar(fd, value)
        return out

    return node(msg)


def connect_kwargs(args) -> dict[str, Any]:
    """The BlitzTrader servers fold long header values across continuation
    lines in the opening handshake, which strict RFC parsers reject. The SDK
    ships a shim for it; reuse it rather than reimplementing."""
    kwargs: dict[str, Any] = {
        "ping_interval": None,  # the app-level text 'ping' is the heartbeat
        "max_size": MAX_FRAME_BYTES,
    }
    ctx = ssl_context(args)
    if ctx is not None:
        kwargs["ssl"] = ctx

    for candidate in (
        Path(__file__).resolve().parent / "blitz-api-py",
        Path(__file__).resolve().parent.parent / "blitz-api-py",
    ):
        if str(candidate) not in sys.path and (
            candidate / "blitzsdk" / "common" / "ws_compat.py"
        ).is_file():
            sys.path.insert(0, str(candidate))
            break
    try:
        from blitzsdk.common.ws_compat import LenientClientConnection

        kwargs["create_connection"] = LenientClientConnection
    except Exception:
        log("ws", "SDK handshake shim not found; using the strict default parser")
    return kwargs


def ssl_context(args):
    """None means 'use the default trust store'."""
    if args.insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        log("tls", "certificate verification DISABLED (--insecure)")
        return ctx
    if args.ca_bundle:
        log("tls", f"using CA bundle {args.ca_bundle}")
        return ssl.create_default_context(cafile=args.ca_bundle)
    return None


# --------------------------------------------------------------------------
# auth
# --------------------------------------------------------------------------


def login(gateway: str, app_key: str, user_id: str, verify: Any = True) -> str:
    url = gateway.rstrip("/") + "/api/app_login"
    log("auth", f"POST {url} as {user_id}")
    try:
        response = requests.post(
            url, json={"appKey": app_key, "userId": user_id}, timeout=20, verify=verify
        )
    except requests.exceptions.SSLError as exc:
        sys.exit(
            f"TLS verification failed for {gateway}: {exc}\n"
            "The UAT certificate is usually signed by an internal CA. Point --ca-bundle at\n"
            "that CA file, or pass --insecure to skip verification (test use only)."
        )
    except requests.RequestException as exc:
        sys.exit(f"Login request failed: {exc}")
    if response.status_code != 200:
        sys.exit(f"Login failed, HTTP {response.status_code}: {response.text[:400]}")
    try:
        body = response.json()
    except ValueError:
        sys.exit(f"Login did not return JSON: {response.text[:400]}")
    token = (body.get("data") or {}).get("accessToken")
    if not token:
        sys.exit(f"No accessToken in login response: {response.text[:400]}")
    return str(token)


# --------------------------------------------------------------------------
# sockets
# --------------------------------------------------------------------------


async def pump(ws, seconds: float, on_message, heartbeat: bool = False) -> Counter:
    """Read frames until the deadline, optionally sending the text ping."""
    counts: Counter = Counter()
    loop = asyncio.get_running_loop()
    deadline = loop.time() + seconds
    next_ping = loop.time() + HEARTBEAT_SECONDS

    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 1.0))
        except asyncio.TimeoutError:
            if heartbeat and loop.time() >= next_ping:
                await ws.send("ping")
                log("i-ws", "sent keep-alive ping")
                next_ping = loop.time() + HEARTBEAT_SECONDS
            continue
        except ConnectionClosed as exc:
            log("ws", f"closed by server (code {exc.code}) {exc.reason}")
            break
        if isinstance(message, bytes):
            message = message.decode("utf-8", "replace")
        on_message(message, counts)
    return counts


async def run_interactive(args, token: str) -> Counter:
    url = (
        f"{args.ws_scheme}://{args.ws_host}/api_interactive/ws"
        + "?"
        + urlencode({"access_token": token})
    )
    log("i-ws", f"connecting to {safe_url(url, token)}")
    payload = json.dumps({"action": args.action})

    def on_message(message: str, counts: Counter) -> None:
        if message == "ping":
            log("i-ws", "<- server ping")
            return
        try:
            event = json.loads(message)
        except ValueError:
            log("i-ws", f"<- non-JSON: {message[:200]}")
            return
        if event.get("type") == "connection":
            log("i-ws", f"<- connected, sessionId={event.get('sessionId')}")
            return
        code = event.get("MessageCode", event.get("messageCode", "?"))
        label = INTERACTIVE_CODES.get(code, "unknown")
        counts[label] += 1
        log("i-ws", f"<- code={code} ({label}) {json.dumps(event, default=str)[:600]}")

    async with websockets.connect(url, **connect_kwargs(args)) as ws:
        log("i-ws", f"connected; sending {payload}")
        await ws.send(payload)
        counts = await pump(ws, args.seconds, on_message, heartbeat=True)
        await ws.send(json.dumps({"action": "AllUnsubscribe"}))
        log("i-ws", "sent AllUnsubscribe; closing")
    return counts


async def run_market_data(args, token: str, pb2, FieldDescriptor) -> Counter:
    url = (
        f"{args.ws_scheme}://{args.ws_host}/md-streaming/ws"
        + "?"
        + urlencode({"key": token})
    )
    log("md-ws", f"connecting to {safe_url(url, token)}")
    payload = json.dumps(
        {"action": "subscribe", "instrumentIds": [args.instrument_id]}
    )
    if pb2 is None:
        log("md-ws", "no protobuf module available; printing raw base64 only")

    def on_message(message: str, counts: Counter) -> None:
        if message == "ping":
            log("md-ws", "<- server ping")
            return
        raw = base64.b64decode(message)
        if pb2 is None:
            counts["undecoded"] += 1
            log("md-ws", f"<- {len(raw)} bytes: {message[:120]}")
            return
        decoded = pb2.MarketDataMessageBase()
        try:
            decoded.ParseFromString(raw)
        except Exception as exc:
            counts["parse error"] += 1
            log("md-ws", f"<- parse error: {exc}")
            return
        kind = decoded.WhichOneof("subtype")
        name = kind if kind else f"untyped(code={decoded.MessageCode})"
        counts[name] += 1
        log("md-ws", f"<- {name} {json.dumps(protobuf_to_dict(decoded, FieldDescriptor))}")

    async with websockets.connect(url, **connect_kwargs(args)) as ws:
        log("md-ws", f"connected; sending {payload}")
        await ws.send(payload)
        counts = await pump(ws, args.seconds, on_message, heartbeat=True)
        await ws.send(
            json.dumps({"action": "unsubscribe", "instrumentIds": [args.instrument_id]})
        )
        log("md-ws", "sent unsubscribe; closing")
    return counts


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="BlitzTrader WebSocket smoke test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Config precedence: command line, then environment, then the Postman\n"
            "collection, then the built-in default.\n\n"
            "Environment: BLITZ_APP_KEY, BLITZ_USER_ID, BLITZ_AUTH_URL,\n"
            "BLITZ_WS_URL (host[:port]), BLITZ_WS_SCHEME, BLITZ_INSTRUMENT_ID,\n"
            "BLITZ_SDK_PATH"
        ),
    )
    p.add_argument(
        "--collection",
        default="BlitzConnect.postman_collection.json",
        help="Postman collection to read variables from (default: %(default)s)",
    )
    p.add_argument(
        "--mode",
        choices=["interactive", "md", "both"],
        default="both",
        help="Which socket(s) to test (default: %(default)s)",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=20.0,
        help="Seconds to listen on each socket (default: %(default)s)",
    )
    p.add_argument(
        "--action",
        default="AllSubscribe",
        help="Interactive subscribe action (default: %(default)s)",
    )
    p.add_argument("--app-key", help="Overrides appKey")
    p.add_argument("--user-id", help="Overrides userId")
    p.add_argument("--gateway", help="Overrides gatewayBaseUrl")
    p.add_argument("--ws-host", help="Overrides wsHost (host[:port], no scheme)")
    p.add_argument("--ws-scheme", choices=["ws", "wss"], help="Overrides wsScheme")
    p.add_argument(
        "--instrument-id", type=int, help="Overrides instrumentId for Market Data"
    )
    p.add_argument(
        "--sdk-path", help="Path to the blitz-api-py repo, for protobuf decoding"
    )
    p.add_argument(
        "--ca-bundle",
        help="PEM file with the CA that signed the server certificate. Needed when a "
        "corporate proxy re-signs TLS, or against a server using an internal CA.",
    )
    p.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS certificate verification, for both login and the sockets. "
        "Test environments only.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved configuration and exit without connecting",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()

    collection: dict[str, str] = {}
    if Path(args.collection).is_file():
        try:
            collection = read_collection_vars(args.collection)
            log("cfg", f"read {len(collection)} variables from {args.collection}")
        except Exception as exc:
            log("cfg", f"could not read {args.collection}: {exc}")
    else:
        log("cfg", f"{args.collection} not found; using defaults and environment")

    args.app_key = pick(args.app_key, "BLITZ_APP_KEY", collection, "appKey", "")
    args.user_id = pick(args.user_id, "BLITZ_USER_ID", collection, "userId", "")
    args.gateway = pick(
        args.gateway,
        "BLITZ_AUTH_URL",
        collection,
        "gatewayBaseUrl",
        "https://uat.bull8.ai:7443/api_gateway/v1",
    )
    args.ws_host = pick(
        args.ws_host, "BLITZ_WS_URL", collection, "wsHost", "uat.bull8.ai:7443"
    )
    args.ws_scheme = pick(
        args.ws_scheme, "BLITZ_WS_SCHEME", collection, "wsScheme", "wss"
    )
    args.instrument_id = int(
        pick(
            str(args.instrument_id) if args.instrument_id else None,
            "BLITZ_INSTRUMENT_ID",
            collection,
            "instrumentId",
            "110010000002885",
        )
    )

    log("cfg", f"gateway    = {args.gateway}")
    log("cfg", f"ws         = {args.ws_scheme}://{args.ws_host}")
    log("cfg", f"instrument = {args.instrument_id}")
    log("cfg", f"listen     = {args.seconds}s per socket, action={args.action}")

    if args.dry_run:
        log("dry-run", f"interactive {args.ws_scheme}://{args.ws_host}/api_interactive/ws"
                       f"?access_token=<JWT>  ->  {json.dumps({'action': args.action})}")
        log("dry-run", f"market data {args.ws_scheme}://{args.ws_host}/md-streaming/ws"
                       f"?key=<JWT>  ->  "
                       f"{json.dumps({'action': 'subscribe', 'instrumentIds': [args.instrument_id]})}")
        return 0

    missing = [n for n, v in (("appKey", args.app_key), ("userId", args.user_id)) if not v]
    if missing:
        sys.exit(
            f"Missing {', '.join(missing)}. Pass --{missing[0]} or set "
            f"{'BLITZ_APP_KEY' if missing[0] == 'appKey' else 'BLITZ_USER_ID'}."
        )

    if args.insecure:
        args.verify = False
    elif args.ca_bundle:
        args.verify = args.ca_bundle
    else:
        args.verify = True

    token = login(args.gateway, args.app_key, args.user_id, verify=args.verify)
    log("auth", f"token {mask(token)}")

    pb2, FieldDescriptor = (None, None)
    if args.mode in ("md", "both"):
        pb2, FieldDescriptor = load_sdk_pb2(args.sdk_path)
        if pb2 is not None:
            log("md-ws", "protobuf decoding enabled")

    results: dict[str, Counter] = {}
    try:
        if args.mode in ("interactive", "both"):
            results["interactive"] = asyncio.run(run_interactive(args, token))
        if args.mode in ("md", "both"):
            results["market data"] = asyncio.run(run_market_data(args, token, pb2, FieldDescriptor))
    except KeyboardInterrupt:
        log("test", "interrupted")
    except InvalidStatus as exc:
        log("test", f"handshake rejected: HTTP {exc.response.status_code} "
                    f"{exc.response.reason_phrase} - wrong host, or bad appKey/userId")
        return 1
    except OSError as exc:
        log("test", f"could not reach {args.ws_host}: {exc}")
        return 1

    print()
    log("result", "=" * 52)
    total = 0
    for name, counts in results.items():
        if not counts:
            log("result", f"{name}: no messages in {args.seconds}s")
        else:
            for kind, count in counts.most_common():
                log("result", f"{name}: {count:>5}  {kind}")
                total += count
    log("result", f"total messages received: {total}")
    if args.mode in ("md", "both") and pb2 is None:
        log("result", "note: pass --sdk-path to decode Market Data protobuf")
    log("result", "=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())

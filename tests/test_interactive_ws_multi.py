import json
import os
import sys
import time
import base64
import threading
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blitzsdk import InteractiveWebSocketClient, InteractiveApiClient
from blitzsdk.interactive.models import OrderRequest

"""
WebSocket multi-connection test case (Interactive API).

Questions under test
--------------------
1. Same user opens multiple WS connections -- does EVERY connection get the
   order response, or only one?  (Expected from API design: only the NEWEST
   connection. The server keeps one browser slot per user and force-closes
   the previous connection when a new one registers.)

2. Keep one connection alive -- does the order response arrive on the
   connected session only?

3. Two different users connected at the same time -- does each user get only
   its own order response (isolation by entityId), or does every connection
   receive everything?

How it is verified
------------------
- The SDK is used ONLY to open connections, receive messages, and place the
  trigger orders (same trade order the other test files use). All scenario
  logic, assertions and logging live in this file.
- A real (UAT, quantity=1, MIS) order is placed to generate a genuine 70000
  order event per user. "Cached" replays (server resends the last message per
  code on subscribe) are separated from "live" events by wall-clock time so a
  replay can never fake a delivery.

Credentials
-----------
User 1: AppKey / UserId / ClientId         (existing test-config.json keys)
User 2: AppKey2 / UserId2 / ClientId2      (optional config keys)
        env overrides: BLITZ_APP_KEY_2 / BLITZ_USER_ID_2 / BLITZ_CLIENT_ID_2
The two-user isolation check is SKIPPED when user 2 is not configured.

Logs to interactive_ws_multi.log. Exit code = number of failed checks.

Usage:
  python tests\test_interactive_ws_multi.py [--no-trigger]
"""

_LOG_FILE = os.path.join(os.path.dirname(__file__), "interactive_ws_multi.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
_log = logging.getLogger(__name__)
print(f"Logging to {_LOG_FILE}")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _cfg = json.load(f)

NO_TRIGGER = "--no-trigger" in sys.argv
WS_URL = _cfg.get("InteractiveWsUrl")
PY_70000 = "70000"

_ORDER = next(i for i in _cfg["Instruments"] if i.get("symbol"))


def creds(n):
    """(app_key, user_id, client_id) for user n (1 or 2). None if missing."""
    app_key = (
        os.getenv(f"BLITZ_APP_KEY_{n}")
        or _cfg.get(f"AppKey{n}" if n > 1 else "AppKey")
        or _cfg.get("AppKey")
    )
    user_id = os.getenv(f"BLITZ_USER_ID_{n}") or _cfg.get(f"UserId{n}" if n > 1 else "UserId")
    client_id = (
        os.getenv(f"BLITZ_CLIENT_ID_{n}")
        or _cfg.get(f"ClientId{n}" if n > 1 else "ClientId")
        or user_id
    )
    return app_key, user_id, client_id


def entity_id_of(ws_client):
    """Decode the entityId claim from the connection's JWT, for logging."""
    token = getattr(ws_client, "token", "")
    if not token:
        return "?"
    parts = token.split(".")
    if len(parts) != 3:
        return "?"
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    payload = payload.replace("-", "+").replace("_", "/")
    try:
        data = json.loads(base64.b64decode(payload))
        return str(data.get("entityId", "?"))
    except Exception:
        return "?"


def wait_until(cond, timeout, step=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(step)
    return False


class CapturingClient:
    """Wraps the SDK WS client, records every connect/close/message event."""

    def __init__(self, label, app_key, user_id, ws_url=None):
        self.label = label
        self.events = []
        self._lock = threading.Lock()
        self.conn_count = 0
        self.connected_event = threading.Event()
        self.client = InteractiveWebSocketClient(
            app_key=app_key, user_id=user_id, ws_url=ws_url or WS_URL
        )
        self.client.set_on_connect(self._on_connect)
        self.client.set_on_message(self._on_message)

    def _record(self, kind, payload):
        with self._lock:
            self.events.append((time.time(), kind, payload))
        _log.info("[%s] %s %s", self.label, kind,
                  json.dumps(payload, default=str)[:400] if not isinstance(payload, str) else payload)

    def _on_connect(self):
        with self._lock:
            self.conn_count += 1
        self.connected_event.set()
        _log.info("[%s] CONNECT (count=%s)", self.label, self.conn_count)
        print(f"  [{self.label}] connected (count={self.conn_count})")
        self.client.subscribe_action("OrderSubscribe")
        _log.info("[%s] OrderSubscribe sent", self.label)

    def _on_message(self, data):
        if isinstance(data, str):
            if data == "ping":
                return
            self._record("raw", data)
            return
        code = data.get("MessageCode", data.get("messageCode", "?"))
        kind = "order70000" if str(code) == PY_70000 else f"code{code}"
        self._record(kind, data)

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def code_70000_since(self, since):
        with self._lock:
            return [e for e in self.events if e[1] == "order70000" and e[0] >= since]

    def count_70000(self):
        return len(self.code_70000_since(0))


def make_api(cred):
    """InteractiveApiClient for a (app_key, user_id, client_id) tuple."""
    app_key, user_id, _client_id = cred
    return InteractiveApiClient(app_key=app_key, user_id=user_id)


def place_order(api, cred):
    """Place one uat order; returns (response, blitz_order_id)."""
    _app_key, _user_id, client_id = cred
    order = OrderRequest(
        instrument_id=_ORDER["id"],
        symbol=f"NSECM|{_ORDER['symbol']}",
        quantity=1,
        price=_cfg["DemoOrderPrice"],
        order_side="BUY",
        order_type="LIMIT",
        product="MIS",
        tif="GFD",
        gtd_date="",  # TiF_GTD_Date is optional on the blitz server
        client_id=client_id,
    )
    r = api.place_order(order)
    js = r if isinstance(r, dict) else {}
    data = js.get("data", {}) if isinstance(js, dict) else {}
    bid = data.get("blitzOrderId") or data.get("blitz_order_id")
    _log.info("[ORDER] placed blitzOrderId=%s response=%s", bid, json.dumps(js, default=str)[:300])
    print(f"  [ORDER] user={client_id} blitzOrderId={bid}")
    return r, bid


def check_takeover(c1, c2):
    """Scenario 1 precondition: the newest connection must close the older one."""
    c2.start()
    ok_connect = wait_until(c2.connected_event.is_set(), 15)
    if not ok_connect:
        print("  [FAIL] SameUser: second (newest) connection never connected")
        _log.error("[FAIL] SameUser: second connection never connected")
        return False

    # sample c1: after the server performs takeover it must drop out of "connected"
    replaced = False
    deadline = time.time() + 4
    while time.time() < deadline and not replaced:
        replaced = not c1.client.connected
        if not replaced:
            time.sleep(0.2)
    # whichever way it went, stop the replaced client from auto-reconnecting
    c1.client.reconnect = False

    if replaced:
        print("  [PASS] SameUser: server replaced/closed the first connection when the second registered")
        _log.info("[PASS] SameUser: first connection closed by server (takeover)")
        if c1.conn_count > 1:
            print(f"  [INFO] SameUser: first connection auto-reconnected {c1.conn_count - 1}x before we stopped it (SDK reconnect flap)")
            _log.info("[INFO] SameUser: reconnect flap seen, conn_count=%s", c1.conn_count)
        return True
    print("  [FAIL] SameUser: first connection stayed open after second registered (no takeover)")
    _log.error("[FAIL] SameUser: no takeover observed")
    return False


def scenario_same_user_two_connections(user1):
    """Q1: multiple connections, same user -- do ALL of them get the order response?"""
    print("\n--- Scenario 1: same user, two connections ---")
    _log.info("--- Scenario 1: same user, two connections ---")
    failures = 0

    c1 = CapturingClient("U1_Conn1", user1[0], user1[1])
    c2 = CapturingClient("U1_Conn2", user1[0], user1[1])
    print(f"  [INFO] entityId = {entity_id_of(c1.client)}")

    c1.start()
    if not wait_until(c1.connected_event.is_set(), 15):
        print("  [FAIL] SameUser: first connection never connected")
        _log.error("[FAIL] SameUser: first connection never connected")
        c1.stop()
        return 1

    takeover = check_takeover(c1, c2)
    failures += 0 if takeover else 1

    time.sleep(1)
    if NO_TRIGGER:
        print(f"  [INFO] --no-trigger: skipping order delivery check (Conn1 70000 count={c1.count_70000()}, Conn2 count={c2.count_70000()})")
    else:
        api = make_api(user1)
        before_c1 = c1.code_70000_since(0)
        before_c2 = c2.code_70000_since(0)
        ts = time.time()
        place_order(api, user1)
        delivered = wait_until(lambda: len(c2.code_70000_since(ts)) >= 1, 12)
        time.sleep(1)  # give a possible (wrong) cross-delivery time to show up

        live_c2 = len(c2.code_70000_since(ts))
        live_c1 = len(c1.code_70000_since(ts))

        if takeover and live_c2 >= 1:
            print(f"  [PASS] SameUser: order response (70000) delivered to the newest connection (Conn2), {live_c2} event(s)")
            _log.info("[PASS] SameUser: order delivered to newest connection")
        elif takeover:
            print("  [FAIL] SameUser: order was placed but no 70000 arrived on the newest connection")
            _log.error("[FAIL] SameUser: no order delivery on newest connection")
            failures += 1
        if live_c1 == 0 and takeover:
            print("  [PASS] SameUser: replaced (closed) connection received NO order response")
            _log.info("[PASS] SameUser: closed connection isolated")
        elif live_c1 > 0:
            print(f"  [FAIL] SameUser: the REPLACED connection still received {live_c1} order response(s)")
            _log.error("[FAIL] SameUser: replaced connection received order responses")
            failures += 1

        print(f"  [INFO] SameUser: Conn1 total 70000={c1.count_70000()} (before trigger={len(before_c1)}), Conn2 total={c2.count_70000()} (before trigger={len(before_c2)})")

    c1.stop()
    c2.stop()
    return failures


def scenario_keep_one_connected(user1):
    """Q2a: with exactly one connection alive, do order responses keep flowing to it?"""
    print("\n--- Scenario 2a: keep ONE connection connected ---")
    _log.info("--- Scenario 2a: keep one connection connected ---")
    c1 = CapturingClient("U1_Keep", user1[0], user1[1])
    c1.start()
    if not wait_until(c1.connected_event.is_set(), 15):
        print("  [FAIL] KeepOne: connection never established")
        _log.error("[FAIL] KeepOne: never connected")
        c1.stop()
        return 1

    time.sleep(1)
    if NO_TRIGGER:
        print(f"  [INFO] --no-trigger: skipping order delivery check (70000 count={c1.count_70000()})")
        c1.stop()
        return 0

    api = make_api(user1)
    ts = time.time()
    place_order(api, user1)
    delivered = wait_until(lambda: len(c1.code_70000_since(ts)) >= 1, 12)
    if delivered:
        print(f"  [PASS] KeepOne: order response arrived on the single connected session ({len(c1.code_70000_since(ts))} event(s))")
        _log.info("[PASS] KeepOne: order delivered to the single connected session")
        c1.stop()
        return 0
    print("  [FAIL] KeepOne: no order response on the connected session")
    _log.error("[FAIL] KeepOne: no order response on connected session")
    c1.stop()
    return 1


def scenario_two_users_isolation(user1, user2):
    """Q2b: two users connected -- is each response isolated to its own user's connection?"""
    print("\n--- Scenario 3: two users, isolation by entityId ---")
    _log.info("--- Scenario 3: two users, isolation by entityId ---")
    if not user2[1]:
        print("  [SKIP] TwoUsers: UserId2 not configured (add AppKey2/UserId2/ClientId2 to test-config.json or set BLITZ_USER_ID_2)")
        _log.info("[SKIP] TwoUsers: second user not configured")
        return 0

    failures = 0
    a = CapturingClient("U1", user1[0], user1[1])
    b = CapturingClient("U2", user2[0], user2[1])
    print(f"  [INFO] user1 entityId = {entity_id_of(a.client)}")
    print(f"  [INFO] user2 entityId = {entity_id_of(b.client)}")

    a.start()
    b.start()
    if not wait_until(a.connected_event.is_set(), 15):
        print("  [FAIL] TwoUsers: user1 never connected")
        failures += 1
    if not wait_until(b.connected_event.is_set(), 15):
        print("  [FAIL] TwoUsers: user2 never connected")
        failures += 1
    if failures:
        a.stop()
        b.stop()
        return failures

    time.sleep(2)

    def deliver(api, cred, whose):
        ts = time.time()
        before_a = len(a.code_70000_since(0))
        before_b = len(b.code_70000_since(0))
        place_order(api, cred)
        ok_target = wait_until(lambda: len(b.code_70000_since(ts) if whose == "B" else a.code_70000_since(ts)) >= 1, 12)
        time.sleep(2)  # negative window: the other user's socket must stay silent
        other = b if whose == "A" else a
        other_got = len(other.code_70000_since(ts))
        deltas = (len(a.code_70000_since(0)) - before_a, len(b.code_70000_since(0)) - before_b)
        return ok_target, other_got, deltas

    api1 = make_api(user1)
    api2 = make_api(user2)

    ok_a, got_b_for_a, delta_a = deliver(api1, user1, "A")
    owned_a = ok_a and got_b_for_a == 0
    print(f"  [{'PASS' if owned_a else 'FAIL'}] TwoUsers: order for user1 -> only user1's connection                                  "
          f"(user1 +{delta_a[0]}, user2 +{delta_a[1]}, user2 leaked {got_b_for_a})")
    _log.info("[%s] TwoUsers: user1 order: user1delta=%s user2delta=%s leak=%s",
              "PASS" if owned_a else "FAIL", delta_a[0], delta_a[1], got_b_for_a)
    failures += 0 if owned_a else 1

    ok_b, got_a_for_b, delta_b = deliver(api2, user2, "B")
    owned_b = ok_b and got_a_for_b == 0
    print(f"  [{'PASS' if owned_b else 'FAIL'}] TwoUsers: order for user2 -> only user2's connection                                  "
          f"(user1 +{delta_b[0]}, user2 +{delta_b[1]}, user1 leaked {got_a_for_b})")
    _log.info("[%s] TwoUsers: user2 order: user1delta=%s user2delta=%s leak=%s",
              "PASS" if owned_b else "FAIL", delta_b[0], delta_b[1], got_a_for_b)
    failures += 0 if owned_b else 1

    a.stop()
    b.stop()
    return failures


def run():
    user1 = creds(1)
    user2 = creds(2)
    print(f"  [INFO] user1 = {user1[1]}, user2 = {user2[1] if user2[1] else '(not configured)'}")
    print(f"  [INFO] ws_url = {WS_URL}, trigger orders = {'OFF' if NO_TRIGGER else 'ON'}")

    failures = 0
    failures += scenario_same_user_two_connections(user1)
    failures += scenario_keep_one_connected(user1)
    failures += scenario_two_users_isolation(user1, user2)

    print(f"\n  PASSED: {6 - failures}   FAILED: {failures}")
    _log.info("SUMMARY: failed=%s", failures)
    return failures


if __name__ == "__main__":
    sys.exit(run())
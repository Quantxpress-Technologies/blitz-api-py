import json
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_LOG_FILE = os.path.join(os.path.dirname(__file__), "interactive_logout.log")
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w",
)
print(f"Logging to {_LOG_FILE}")

import requests

from blitzsdk import InteractiveApiClient

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test-config.json")

with open(CONFIG_PATH) as f:
    _conn = json.load(f)


def _pp(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    print("--- Interactive API Test: profile / holdings / logout (SAM001) ---")

    client = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    print(f"  [INFO] Logged in via gateway, token: {client.token[:40]}...")
    old_token = client.token

    holdings = client.get_holdings()
    print(f"  [PASS] get_holdings -> {len(holdings) if isinstance(holdings, list) else holdings}")

    profile = client.get_profile()
    print("  [PASS] get_profile ->")
    _pp(profile)

    resp = client.logout()
    print(f"  [PASS] logout -> {json.dumps(resp, indent=2, default=str)}")
    assert isinstance(resp, dict) and resp.get("message"), f"Unexpected logout response: {resp}"

    r_raw = requests.post(
        f"{client.base_url}/session/logout",
        json={},
        headers={
            "Authorization": f"Bearer {old_token}",
            "Content-Type": "application/json",
        },
        timeout=15,
        verify=False,
    )
    print(f"  [INFO] Reusing revoked token -> HTTP {r_raw.status_code}: {r_raw.text}")
    assert r_raw.status_code == 401, f"Expected 401 for revoked token, got {r_raw.status_code}"

    client2 = InteractiveApiClient(app_key=_conn["AppKey"], user_id=_conn["UserId"])
    p2 = client2.get_profile()
    print("  [PASS] Fresh login after logout still works")

    print("  ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
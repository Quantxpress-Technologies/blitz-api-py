import json
import logging

from .config import Config
from .exceptions import AuthenticationError
from .session import build_session

logger = logging.getLogger(__name__)

_SESSION = build_session()


class AuthClient:
    def __init__(self, app_key: str, user_id: str, auth_base_url: str | None = None):
        self.app_key = app_key
        self.user_id = user_id
        self.auth_base_url = (auth_base_url or Config.AUTH_BASE_URL).rstrip("/")
        self.access_token = None

    def login(self):
        url = f"{self.auth_base_url}/api/app_login"
        headers = {"Content-Type": "application/json", "Accept": "*/*"}
        payload = {"appKey": self.app_key, "userId": self.user_id}

        logger.info("[AUTH] POST %s", url)
        logger.info("[AUTH] Payload: %s", json.dumps(payload))

        try:
            response = _SESSION.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        except Exception as e:
            raise AuthenticationError(f"Login failed: {e}")

        logger.info("[AUTH] Response: %s", response.status_code)
        if response.status_code != 200:
            raise AuthenticationError(f"Login failed ({response.status_code}): {response.text}")

        data = response.json()
        logger.info("[AUTH] Body: %s", json.dumps(data, default=str)[:500])
        if data.get("status") != "success":
            raise AuthenticationError(f"Login failed: {data.get('message', 'unknown')}")

        self.access_token = data["data"]["accessToken"]
        logger.info("Login successful.")
        return self.access_token

    def get_token(self):
        if not self.access_token:
            self.login()
        return self.access_token

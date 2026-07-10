import requests
import logging

from .config import Config
from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)


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

        try:
            response = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
        except requests.exceptions.Timeout:
            raise AuthenticationError("Server timeout. UAT server may be down.")
        except requests.exceptions.ConnectionError:
            raise AuthenticationError("Cannot connect to server.")
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Request failed: {e}")

        if response.status_code != 200:
            raise AuthenticationError(f"Login failed ({response.status_code}): {response.text}")

        data = response.json()
        if data.get("status") != "success":
            raise AuthenticationError(f"Login failed: {data.get('message', 'unknown')}")

        self.access_token = data["data"]["accessToken"]
        logger.info("Login successful.")
        return self.access_token

    def get_token(self):
        if not self.access_token:
            self.login()
        return self.access_token

import json
import logging

import requests

from .auth import AuthClient
from .config import Config
from .exceptions import RequestError
from .session import build_session

logger = logging.getLogger(__name__)

_SESSION = build_session()


class BaseApiClient:
    def __init__(self, app_key: str, user_id: str, base_url: str | None = None, auth: AuthClient | None = None):
        self.auth = auth or AuthClient(app_key, user_id)
        self.token = self.auth.get_token()
        self.base_url = (base_url or self._default_base_url()).rstrip("/")

    def _default_base_url(self) -> str:
        return ""

    def _ensure_logged_in(self):
        self.token = self.auth.get_token()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

    def _request(self, method: str, endpoint: str, payload=None, params=None, base_url: str | None = None, retries=0):
        url = f"{(base_url or self.base_url)}/{endpoint.lstrip('/')}"
        logger.info("[REQ] %s %s", method, url)
        if payload:
            logger.info("[REQ] Payload: %s", json.dumps(payload, default=str)[:2000])
        if params:
            logger.info("[REQ] Params: %s", params)
        try:
            response = _SESSION.request(
                method, url,
                data=json.dumps(payload) if payload is not None else None,
                params=params, headers=self._headers(), timeout=15
            )
        except requests.exceptions.ConnectionError as e:
            logger.error("[REQ] ConnectionError: %s", e)
            raise RequestError(0, "Server not reachable")
        except requests.exceptions.Timeout as e:
            logger.error("[REQ] Timeout: %s", e)
            raise RequestError(0, "Request timed out")

        logger.info("[RES] %s %s -> %s", method, endpoint, response.status_code)
        resp_text = response.text[:2000]
        logger.info("[RES] Body: %s", resp_text)

        if response.status_code == 401 and retries < 1:
            logger.warning("Token expired, re-logging in...")
            self._ensure_logged_in()
            return self._request(method, endpoint, payload, params, base_url, retries + 1)

        if response.status_code not in (200, 201):
            text = response.text[:500]
            raise RequestError(response.status_code, f"{method} {endpoint} failed", text)

        try:
            parsed = response.json()
        except ValueError:
            parsed = None
        return {
            "status_code": response.status_code,
            "response_text": response.text,
            "response_json": parsed,
            "headers": dict(response.headers),
        }

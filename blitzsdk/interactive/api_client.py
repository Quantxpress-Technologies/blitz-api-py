import logging

from ..common.auth import AuthClient
from ..common.config import Config
from ..common.exceptions import RequestError
from .models import OrderRequest

logger = logging.getLogger(__name__)


class InteractiveApiClient:
    def __init__(self, app_key: str, user_id: str):
        self.app_key = app_key
        self.user_id = user_id
        self.auth = AuthClient(app_key, user_id)
        self.token = None
        self._ensure_logged_in()

    def _ensure_logged_in(self):
        self.token = self.auth.get_token()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

    def _request(self, method: str, endpoint: str, payload=None, params=None, retries=0):
        url = f"{Config.API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        import requests

        try:
            response = requests.request(
                method, url, json=payload, params=params, headers=self._headers(), verify=False, timeout=15
            )
        except requests.exceptions.ConnectionError:
            raise RequestError(0, "API server not reachable")
        except requests.exceptions.Timeout:
            raise RequestError(0, "Request timed out")

        if response.status_code == 401 and retries < 1:
            logger.warning("Token expired, re-logging in...")
            self._ensure_logged_in()
            return self._request(method, endpoint, payload, params, retries + 1)

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

    def get_orders(self):
        return self._request("GET", "orders")

    def get_open_orders(self):
        return self._request("GET", "orders/openOrders")

    def get_order_by_blitz_id(self, blitz_id: int):
        return self._request("GET", f"orders/{blitz_id}")

    def get_positions(self):
        return self._request("GET", "positions")

    def get_trades(self):
        return self._request("GET", "trades")

    def get_statistics(self):
        return self._request("GET", "strategy/statistics")

    def place_order(self, order: OrderRequest | dict):
        data = order.to_dict() if isinstance(order, OrderRequest) else order
        return self._request("POST", "orders/placeOrder", payload=data)

    def modify_order(self, data: dict):
        return self._request("PUT", "orders/modifyOrder", payload=data)

    def cancel_order(self, instrument_id: int, blitz_order_id: int):
        params = {"instrumentId": instrument_id, "blitzOrderId": blitz_order_id}
        return self._request("DELETE", "orders/cancelOrder", params=params)

    def send_signals(self, signals: list):
        return self._request("POST", "signals", payload=signals)

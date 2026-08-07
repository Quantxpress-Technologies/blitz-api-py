import logging

from ..common.base_client import BaseApiClient
from ..common.config import Config
from .models import OrderRequest

logger = logging.getLogger(__name__)


class InteractiveApiClient(BaseApiClient):
    def default_base_url(self) -> str:
        return Config.API_BASE_URL

    def get_orders(self):
        return self.request("GET", "orders")

    def get_open_orders(self):
        return self.request("GET", "orders/openOrders")

    def get_order_by_blitz_id(self, blitz_id: int):
        return self.request("GET", f"orders/{blitz_id}")

    def get_positions(self):
        return self.request("GET", "positions")

    def get_trades(self):
        return self.request("GET", "trades")

    def get_statistics(self):
        return self.request("GET", "strategy/statistics")

    def get_statistics_by_instance(self, strategy_name: str, strategy_instance_name: str):
        params = {
            "strategyName": strategy_name,
            "strategyInstanceName": strategy_instance_name,
        }
        return self.request("GET", "strategy/statistics/instance", params=params)

    def place_order(self, order: OrderRequest | dict):
        data = order.to_dict() if isinstance(order, OrderRequest) else order
        return self.request("POST", "orders/placeOrder", payload=data)

    def modify_order(self, data: dict):
        return self.request("PUT", "orders/modifyOrder", payload=data)

    def cancel_order(self, instrument_id: int, blitz_order_id: int):
        params = {"instrumentId": instrument_id, "blitzOrderId": blitz_order_id}
        return self.request("DELETE", "orders/cancelOrder", params=params)

    def send_signals(self, signals: list):
        return self.request("POST", "signals", payload=signals)

import time

from ..common.config import Config


class OrderRequest:
    def __init__(
        self,
        instrument_id: int,
        symbol: str,
        quantity: int,
        price: float,
        order_side: str,
        order_type: str,
        product: str,
        tif: str,
        gtd_date: str,
        client_id: str | None = None,
        disclosed_quantity: int = 0,
        stop_price: float = 0,
    ):
        self.instrument_id = instrument_id
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.order_side = order_side
        self.order_type = order_type
        self.product = product
        self.tif = tif
        self.gtd_date = gtd_date
        self.client_id = client_id or Config.CLIENT_ID
        self.disclosed_quantity = disclosed_quantity
        self.stop_price = stop_price

    def to_dict(self):
        return {
            "CorrelationOrderId": f"order_{int(time.time() * 1000)}",
            "Quantity": self.quantity,
            "Product": self.product,
            "TIF": self.tif,
            "Price": self.price,
            "OrderType": self.order_type,
            "OrderSide": self.order_side,
            "DisclosedQuantity": self.disclosed_quantity,
            "StopPrice": self.stop_price,
            "ClientId": self.client_id,
            "TiF_GTD_Date": self.gtd_date,
            "InstrumentId": self.instrument_id,
            "Symbol": None,
        }

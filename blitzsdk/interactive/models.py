import time


class OrderRequest:
    def __init__(
        self,
        instrument_id: int,
        symbol: str,
        quantity: int = 1,
        price: float = 11,
        order_side: str = "BUY",
        order_type: str = "LIMIT",
        product: str = "MIS",
        tif: str = "GFD",
        client_id: str = "Prateek123",
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
        self.client_id = client_id
        self.disclosed_quantity = disclosed_quantity
        self.stop_price = stop_price

    def to_dict(self):
        return {
            "correlationOrderId": f"order_{int(time.time() * 1000)}",
            "quantity": self.quantity,
            "product": self.product,
            "tif": self.tif,
            "price": self.price,
            "orderType": self.order_type,
            "instrumentId": self.instrument_id,
            "symbol": self.symbol,
            "orderSide": self.order_side,
            "disclosedQuantity": self.disclosed_quantity,
            "stopPrice": self.stop_price,
            "clientId": self.client_id,
            "tiF_GTD_Date": "2025-10-10",
        }

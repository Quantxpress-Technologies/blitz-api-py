import logging

from ..common.base_client import BaseApiClient
from ..common.config import Config

logger = logging.getLogger(__name__)


_INSTRUMENT_BASE = Config.INSTRUMENT_URL.replace("/gz/download", "")


class MarketDataApiClient(BaseApiClient):
    def default_base_url(self) -> str:
        return Config.MD_API_URL

    def get_instrument_by_id(self, instrument_id: int):
        return self.request("GET", str(instrument_id), base_url=_INSTRUMENT_BASE)

    def get_instrument_by_symbol(self, symbol: str):
        return self.request("GET", symbol.replace('|', ':'), base_url=_INSTRUMENT_BASE)

    def get_ltp(self, instrument_ids: list):
        return self.request("POST", "marketfeed/ltp", payload={"InstrumentIds": instrument_ids})

    def get_option_chain(self, symbol: str, expiry: str):
        return self.request("POST", "marketfeed/optionChain", payload={"Symbol": symbol, "ExpiryDate": expiry})

    def get_quote(self, instrument_ids: list):
        return self.request("POST", "marketfeed/quote", payload={"InstrumentIds": instrument_ids})

    def get_historical_data(self, instrument: str, interval: str):
        return self.request("POST", "marketfeed/historicalData", payload={"Instrument": instrument, "interval": interval})

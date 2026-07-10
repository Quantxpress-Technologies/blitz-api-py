import logging
import requests

from ..common.auth import AuthClient
from ..common.config import Config
from ..common.exceptions import RequestError

logger = logging.getLogger(__name__)


class MarketDataApiClient:
    def __init__(self, app_key: str, user_id: str):
        self.auth = AuthClient(app_key, user_id)
        self.token = self.auth.get_token()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

    def _get(self, path: str):
        url = f"{Config.MD_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
        try:
            r = requests.get(url, headers=self._headers(), verify=False, timeout=15)
            if r.status_code != 200:
                raise RequestError(r.status_code, f"GET {path}", r.text[:500])
            try:
                parsed = r.json()
            except ValueError:
                parsed = None
            return {
                "status_code": r.status_code,
                "response_text": r.text,
                "response_json": parsed,
                "headers": dict(r.headers),
            }
        except requests.exceptions.ConnectionError:
            raise RequestError(0, "Server not reachable")

    def _post(self, path: str, payload: dict):
        url = f"{Config.MD_API_URL.rstrip('/')}/{path.lstrip('/')}"
        try:
            r = requests.post(url, json=payload, headers=self._headers(), verify=False, timeout=15)
            if r.status_code != 200:
                raise RequestError(r.status_code, f"POST {path}", r.text[:500])
            try:
                parsed = r.json()
            except ValueError:
                parsed = None
            return {
                "status_code": r.status_code,
                "response_text": r.text,
                "response_json": parsed,
                "headers": dict(r.headers),
            }
        except requests.exceptions.ConnectionError:
            raise RequestError(0, "Server not reachable")

    def get_instrument_by_id(self, instrument_id: int):
        return self._get(f"v1/api/instruments/{instrument_id}")

    def get_instrument_by_symbol(self, symbol: str):
        return self._get(f"v1/api/instruments/{symbol.replace('|', ':')}")

    def get_ltp(self, instrument_ids: list):
        return self._post("marketfeed/ltp", {"InstrumentIds": instrument_ids})

    def get_option_chain(self, symbol: str, expiry: str):
        return self._post("marketfeed/optionChain", {"symbol": symbol, "expiryDate": expiry})

    def get_quote(self, instrument_ids: list):
        return self._post("marketfeed/quote", {"InstrumentIds": instrument_ids})

    def get_historical_data(self, instrument: str, interval: str):
        return self._post("marketfeed/historicalData", {"Instrument": instrument, "interval": interval})

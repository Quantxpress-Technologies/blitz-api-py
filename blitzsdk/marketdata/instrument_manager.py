import requests
import gzip
import json

from ..common.config import Config


class InstrumentManager:
    _cache: dict[str, int] = {}
    _id_cache: dict[int, str] = {}

    @classmethod
    def load(cls, url: str | None = None):
        url = url or Config.INSTRUMENT_URL
        response = requests.get(url, timeout=15)
        decompressed = gzip.decompress(response.content)
        data = json.loads(decompressed)
        cls._cache = {
            f'{item["exchangeSegment"]}|{item["instrumentName"]}': item["instrumentId"]
            for item in data
        }
        cls._id_cache = {iid: name for name, iid in cls._cache.items()}

    @classmethod
    def resolve(cls, symbol: str | None = None, instrument_id: int | None = None) -> int:
        if not cls._cache:
            cls.load()
        if symbol and instrument_id is None:
            result = cls._cache.get(symbol)
            if not result:
                raise ValueError(f"Instrument not found: {symbol}")
            return result
        if instrument_id is not None and not symbol:
            return instrument_id
        if symbol and instrument_id is not None:
            expected = cls._cache.get(symbol)
            if expected and expected != instrument_id:
                raise ValueError(f"ID mismatch: {instrument_id} != {expected}")
            return instrument_id
        raise ValueError("Provide symbol or instrument_id")

    @classmethod
    def resolve_ids(cls, items: list) -> list[int]:
        resolved = []
        for x in items:
            if isinstance(x, int):
                resolved.append(x)
            elif isinstance(x, str):
                if x.isdigit():
                    resolved.append(int(x))
                else:
                    parts = x.split("|")
                    if len(parts) < 2:
                        raise ValueError(f"Use EXCHANGE|NAME format, got: {x}")
                    resolved.append(cls.resolve(symbol=f"{parts[0]}|{parts[1]}"))
            else:
                resolved.append(x)
        return resolved

    @classmethod
    def count(cls) -> int:
        return len(cls._cache)

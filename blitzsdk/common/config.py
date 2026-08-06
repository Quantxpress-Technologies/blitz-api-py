import json
import os


def find_config():
    env_path = os.getenv("BLITZ_CONFIG_PATH")
    if env_path:
        abs_path = os.path.abspath(env_path)
        if os.path.exists(abs_path):
            return abs_path
    here = os.path.dirname(os.path.abspath(__file__))
    pkg_root = os.path.dirname(here)
    tests_path = os.path.normpath(os.path.join(pkg_root, "..", "tests", "test-config.json"))
    if os.path.exists(tests_path):
        return tests_path
    return None


_config_path = find_config()
_conn = {}
if _config_path:
    with open(_config_path, encoding="utf-8") as f:
        _conn = json.load(f)


def get_config(key, env_var):
    return os.getenv(env_var) or _conn.get(key, "")


class Config:
    AUTH_BASE_URL = get_config("AuthBaseUrl", "BLITZ_AUTH_URL")
    API_BASE_URL = get_config("InteractiveApiUrl", "BLITZ_API_URL")
    WS_URL = get_config("InteractiveWsUrl", "BLITZ_WS_URL")
    MD_API_URL = get_config("MarketDataApiUrl", "BLITZ_MD_API_URL")
    MD_WS_URL = get_config("MarketDataWsUrl", "BLITZ_MD_WS_URL")
    INSTRUMENT_URL = get_config("InstrumentGzUrl", "BLITZ_INSTRUMENT_URL")

    APP_KEY = get_config("AppKey", "BLITZ_APP_KEY")
    USER_ID = get_config("UserId", "BLITZ_USER_ID")
    CLIENT_ID = get_config("ClientId", "BLITZ_CLIENT_ID")

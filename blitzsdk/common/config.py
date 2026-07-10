import os


class Config:
    AUTH_BASE_URL = os.getenv("BLITZ_AUTH_URL", "http://uat.bull8.ai:7443/api_gateway/v1")
    API_BASE_URL = os.getenv("BLITZ_API_URL", "http://uat.bull8.ai:7443/api_interactive/api/v1")
    WS_URL = os.getenv("BLITZ_WS_URL", "ws://uat.bull8.ai:7443/api_interactive/ws")
    MD_API_URL = os.getenv("BLITZ_MD_API_URL", "http://uat.bull8.ai:7443/md-api")
    MD_WS_URL = os.getenv("BLITZ_MD_WS_URL", "ws://uat.bull8.ai:7443/md-streaming/ws")
    INSTRUMENT_URL = os.getenv("BLITZ_INSTRUMENT_URL", "http://uat.bull8.ai:7443/v1/api/instruments/gz/download")
    BASE_URL = os.getenv("BLITZ_BASE_URL", "http://uat.bull8.ai:7443")
    MD_BASE_URL = os.getenv("BLITZ_MD_BASE_URL", "http://uat.bull8.ai:7443")

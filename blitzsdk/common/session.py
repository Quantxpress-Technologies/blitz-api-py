import json
import warnings

import requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def build_session():
    session = requests.Session()
    session.verify = False
    return session

from .config import Config
from .auth import AuthClient
from .exceptions import BlitzSDKException, AuthenticationError, RequestError
from .base_client import BaseApiClient
from .base_ws_client import BaseWebSocketClient

import websocket._http as _ws_http
import websocket._handshake as _ws_handshake
import websocket._abnf as _ws_abnf

_original_validate = _ws_abnf.ABNF.validate


def _patched_validate(self, skip_utf8_validation=False):
    if self.opcode not in _ws_abnf.ABNF.OPCODES:
        raise _ws_abnf.WebSocketProtocolException("Invalid opcode %r", self.opcode)
    if self.opcode == _ws_abnf.ABNF.OPCODE_PING and not self.fin:
        raise _ws_abnf.WebSocketProtocolException("Invalid ping frame.")
    if self.opcode == _ws_abnf.ABNF.OPCODE_CLOSE:
        l = len(self.data)
        if not l:
            return
        if l == 1 or l >= 126:
            raise _ws_abnf.WebSocketProtocolException("Invalid close frame.")
        if l > 2 and not skip_utf8_validation and not _ws_abnf.validate_utf8(self.data[2:]):
            raise _ws_abnf.WebSocketProtocolException("Invalid close frame.")
        code = 256 * int(self.data[0]) + int(self.data[1])
        if not _ws_abnf.ABNF._is_valid_close_status(code):
            raise _ws_abnf.WebSocketProtocolException("Invalid close opcode %r", code)


def _patch_websocket_read_headers():
    def _patched_read_headers(sock):
        status = None
        status_message = None
        headers = {}
        last_key = None

        while True:
            raw = _ws_http.recv_line(sock).decode("utf-8")
            stripped = raw.strip()
            if not stripped:
                break
            if status is None:
                status_info = stripped.split(" ", 2)
                status = int(status_info[1])
                if len(status_info) > 2:
                    status_message = status_info[2]
            elif raw[0] in (" ", "\t") and last_key:
                headers[last_key] += " " + stripped
            else:
                kv = stripped.split(":", 1)
                if len(kv) == 2:
                    key, value = kv
                    key_lower = key.lower()
                    if key_lower == "set-cookie" and headers.get("set-cookie"):
                        headers["set-cookie"] += "; " + value.strip()
                    else:
                        headers[key_lower] = value.strip()
                    last_key = key_lower

        return status, headers, status_message

    _ws_http.read_headers = _patched_read_headers
    _ws_handshake.read_headers = _patched_read_headers


_patch_websocket_read_headers()
_ws_abnf.ABNF.validate = _patched_validate

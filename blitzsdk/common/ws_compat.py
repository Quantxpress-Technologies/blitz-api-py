
from __future__ import annotations

import re
from collections.abc import Callable, Generator

from websockets.asyncio.client import ClientConnection
from websockets.client import ClientProtocol
from websockets.datastructures import Headers
from websockets.exceptions import InvalidHandshake, InvalidMessage
from websockets.http11 import MAX_LINE_LENGTH, MAX_NUM_HEADERS, Response, d
from websockets.protocol import CONNECTING, OPEN

_token_re = re.compile(rb"[-!#$%&\'*+.^_`|~0-9a-zA-Z]+")
_value_re = re.compile(rb"[\x09\x20-\x7e\x80-\xff]*")


def _parse_line(read_line: Callable[[int], Generator[None, None, bytes]]) -> Generator[None, None, bytes]:
    line = yield from read_line(MAX_LINE_LENGTH)
    if not line.endswith(b"\r\n"):
        raise EOFError("line without CRLF")
    return line[:-2]


def _read_response_lenient(
    read_line: Callable[[int], Generator[None, None, bytes]],
) -> Generator[None, None, Response]:
    """
    Parse an HTTP response, tolerating obsolete line folding (obs-fold).

    Some servers fold header values onto continuation lines that start with
    SP or HTAB. Strict parsers reject these; this one appends each
    continuation to the previous header value, like .NET's ClientWebSocket.
    """
    status_line = yield from _parse_line(read_line)

    try:
        protocol, raw_status_code, raw_reason = status_line.split(b" ", 2)
    except ValueError:
        raise ValueError(f"invalid HTTP status line: {d(status_line)}") from None
    if protocol != b"HTTP/1.1":
        raise ValueError(f"unsupported protocol; expected HTTP/1.1: {d(status_line)}")
    try:
        status_code = int(raw_status_code)
    except ValueError:
        raise ValueError(
            f"invalid status code; expected integer; got {d(raw_status_code)}"
        ) from None
    if not 100 <= status_code < 600:
        raise ValueError(
            f"invalid status code; expected 100-599; got {d(raw_status_code)}"
        )
    reason = raw_reason.decode("ascii", "surrogateescape")

    names: list[str] = []
    values: dict[str, str] = {}
    for _ in range(MAX_NUM_HEADERS + 1):
        line = yield from _parse_line(read_line)
        if line == b"":
            break
        # Obs-fold continuation line: starts with SP or HTAB.
        if line[:1] in (b" ", b"\t"):
            if not names:
                raise ValueError(f"invalid HTTP header line: {d(line)}")
            name = names[-1]
            continuation = line.strip().decode("ascii", "surrogateescape")
            values[name] = f"{values[name]} {continuation}"
            continue

        try:
            raw_name, raw_value = line.split(b":", 1)
        except ValueError:
            raise ValueError(f"invalid HTTP header line: {d(line)}") from None
        if not _token_re.fullmatch(raw_name):
            raise ValueError(f"invalid HTTP header name: {d(raw_name)}")
        raw_value = raw_value.strip(b" \t")
        if not _value_re.fullmatch(raw_value):
            raise ValueError(f"invalid HTTP header value: {d(raw_value)}")

        name = raw_name.decode("ascii")
        value = raw_value.decode("ascii", "surrogateescape")
        if name in values:
            values[name] = f"{values[name]}, {value}"
        else:
            values[name] = value
            names.append(name)

    headers = Headers()
    for name in names:
        headers[name] = values[name]

    return Response(status_code, reason, headers)


class LenientClientProtocol(ClientProtocol):
    """
    ClientProtocol that accepts obs-fold in the opening handshake response.
    """

    def parse(self) -> Generator[None]:
        if self.state is CONNECTING:
            try:
                response = yield from _read_response_lenient(self.reader.read_line)
            except Exception as exc:
                self.handshake_exc = InvalidMessage(
                    "did not receive a valid HTTP response"
                )
                self.handshake_exc.__cause__ = exc
                self.send_eof()
                self.parser = self.discard()
                next(self.parser)
                yield

            if self.debug:
                code, phrase = response.status_code, response.reason_phrase
                self.logger.debug("< HTTP/1.1 %d %s", code, phrase)
                for key, value in response.headers.raw_items():
                    self.logger.debug("< %s: %s", key, value)

            try:
                self.process_response(response)
            except InvalidHandshake as exc:
                response._exception = exc
                self.events.append(response)
                self.handshake_exc = exc
                self.send_eof()
                self.parser = self.discard()
                next(self.parser)
                yield

            assert self.state is CONNECTING
            self.state = OPEN
            self.events.append(response)

        yield from super().parse()


class LenientClientConnection(ClientConnection):
    """
    ClientConnection that builds a LenientClientProtocol for the handshake.
    """

    def __init__(self, protocol: ClientProtocol, **kwargs):
        if not isinstance(protocol, LenientClientProtocol):
            protocol = LenientClientProtocol(
                protocol.uri,
                origin=protocol.origin,
                extensions=protocol.available_extensions,
                subprotocols=protocol.available_subprotocols,
                max_size=protocol.max_size,
                logger=protocol.logger,
            )
        super().__init__(protocol, **kwargs)

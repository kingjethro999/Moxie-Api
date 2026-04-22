from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from moxie.types import Receive, Scope, Send

T = TypeVar("T")

class Request:
    __slots__ = ("scope", "_receive", "_body", "_json", "_form", "_headers")

    def __init__(self, scope: Scope, receive: Receive) -> None:
        self.scope = scope
        self._receive = receive
        self._body: bytes | None = None
        self._json: Any = None
        self._form: dict[str, Any] | None = None
        self._headers: dict[str, str] | None = None

    @property
    def method(self) -> str:
        return self.scope["method"]

    @property
    def path(self) -> str:
        return self.scope["path"]

    @property
    def query_params(self) -> dict[str, Any]:
        from urllib.parse import parse_qs
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        return {
            k: v[0] if len(v) == 1 else v
            for k, v in parse_qs(query_string).items()
        }

    @property
    def headers(self) -> dict[str, str]:
        if self._headers is None:
            self._headers = {
                k.decode("latin-1").lower(): v.decode("latin-1")
                for k, v in self.scope.get("headers", [])
            }
        return self._headers

    async def body(self) -> bytes:
        if self._body is None:
            chunks = []
            while True:
                message = await self._receive()
                if message["type"] == "http.request":
                    chunks.append(message.get("body", b""))
                    if not message.get("more_body", False):
                        break
            self._body = b"".join(chunks)
        return self._body

    async def json(self) -> Any:
        if self._json is None:
            body = await self.body()
            self._json = json.loads(body)
        return self._json

    async def form(self) -> dict[str, Any]:
        if self._form is None:
            content_type = self.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                from urllib.parse import parse_qs
                body = await self.body()
                self._form = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in parse_qs(body.decode("utf-8")).items()
                }
            elif "multipart/form-data" in content_type:
                try:
                    import multipart  # noqa: F401
                except ImportError:
                    raise RuntimeError(
                        "python-multipart is required for multipart/form-data support"
                    ) from None
                
                # Simplified implementation for now
                self._form = {} # In a real implementation, we'd parse the stream
            else:
                self._form = {}
        return self._form

class WebSocket:
    __slots__ = ("scope", "_receive", "_send", "state")

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self.state: dict[str, Any] = {}

    async def accept(self, subprotocol: str | None = None) -> None:
        message = {"type": "websocket.accept"}
        if subprotocol:
            message["subprotocol"] = subprotocol
        await self._send(message)

    async def receive_text(self) -> str:
        message = await self._receive()
        return message["text"]

    async def receive_bytes(self) -> bytes:
        message = await self._receive()
        return message["bytes"]

    async def receive_json(self, model: type[T] | None = None) -> dict[str, Any] | T:
        message = await self._receive()
        data = json.loads(message["text"])
        if model:
            from pydantic import TypeAdapter
            return TypeAdapter(model).validate_python(data)
        return data

    async def iter_json(
        self, model: type[T] | None = None
    ) -> AsyncIterator[dict[str, Any] | T]:
        while True:
            try:
                yield await self.receive_json(model)
            except Exception:
                break

    async def send_text(self, data: str) -> None:
        await self._send({"type": "websocket.send", "text": data})

    async def send_bytes(self, data: bytes) -> None:
        await self._send({"type": "websocket.send", "bytes": data})

    async def send_json(self, data: Any) -> None:
        from moxie.utils.encoding import json_dumps
        await self._send({"type": "websocket.send", "text": json_dumps(data)})

    async def close(self, code: int = 1000) -> None:
        await self._send({"type": "websocket.close", "code": code})

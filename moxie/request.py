import json
from typing import Any, Dict, Optional, Union
from urllib.parse import parse_qs
from moxie.types import Receive, Scope

class Request:
    __slots__ = ("scope", "_receive", "_body", "_json", "_form")

    def __init__(self, scope: Scope, receive: Receive) -> None:
        self.scope = scope
        self._receive = receive
        self._body: Optional[bytes] = None
        self._json: Any = None
        self._form: Optional[Dict[str, Any]] = None

    @property
    def method(self) -> str:
        return self.scope["method"]

    @property
    def path(self) -> str:
        return self.scope["path"]

    @property
    def query_params(self) -> Dict[str, Union[str, list[str]]]:
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(query_string).items()}

    @property
    def headers(self) -> Dict[str, str]:
        if not hasattr(self, "_headers"):
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

    async def form(self) -> Dict[str, Any]:
        if self._form is None:
            body = await self.body()
            content_type = self.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                self._form = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in parse_qs(body.decode("utf-8")).items()
                }
            else:
                self._form = {}
        return self._form

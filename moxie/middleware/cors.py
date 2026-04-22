from typing import Any

from moxie.middleware.base import ASGIMiddleware
from moxie.response import PlainTextResponse, Response


class CORSMiddleware(ASGIMiddleware):
    def __init__(
        self,
        app: Any,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        allow_credentials: bool = False,
        expose_headers: list[str] | None = None,
        max_age: int = 600,
    ) -> None:
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
        ]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode("latin-1")

        if not origin:
            await self.app(scope, receive, send)
            return

        if method == "OPTIONS" and b"access-control-request-method" in headers:
            # Preflight request
            response = self.preflight_response(origin, headers)
            await response(send)
            return

        # Regular request
        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = self.extend_headers(
                    message.get("headers", []), origin
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def preflight_response(
        self, origin: str, request_headers: dict[bytes, bytes]
    ) -> Response:
        headers: dict[str, str] = {
            "Access-Control-Max-Age": str(self.max_age),
        }

        if "*" in self.allow_origins:
            headers["Access-Control-Allow-Origin"] = "*"
        elif origin in self.allow_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        else:
            return PlainTextResponse("CORS Origin Not Allowed", status_code=403)

        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

        return PlainTextResponse("", status_code=204, headers=headers)

    def extend_headers(
        self, headers: list[tuple[bytes, bytes]], origin: str
    ) -> list[tuple[bytes, bytes]]:
        new_headers = list(headers)
        
        # Access-Control-Allow-Origin
        if "*" in self.allow_origins:
            new_headers.append((b"access-control-allow-origin", b"*"))
        elif origin in self.allow_origins:
            new_headers.append(
                (b"access-control-allow-origin", origin.encode("latin-1"))
            )
            new_headers.append((b"vary", b"Origin"))

        if self.allow_credentials:
            new_headers.append((b"access-control-allow-credentials", b"true"))

        if self.expose_headers:
            header_val = ", ".join(self.expose_headers).encode("latin-1")
            new_headers.append((b"access-control-expose-headers", header_val))

        return new_headers

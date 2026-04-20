from collections.abc import Awaitable, Callable
from typing import Any

from moxie.request import Request
from moxie.response import Response

CallNext = Callable[[Request], Awaitable[Response]]

class BaseMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        
        async def call_next(req: Request) -> Response:
            # This is a bit tricky in ASGI. Usually, middleware wraps the 
            # entire ASGI app and provides a custom 'send' or similar.
            # But the 'call_next' pattern from FastAPI/Starlette is popular.
            
            # Simplified for now: just call the app and capture the response
            # (In a real implementation, we'd need a more complex capture mechanism)
            return await self._execute_app_and_capture_response(scope, receive)

        response = await self.dispatch(request, call_next)
        await response(send)

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        raise NotImplementedError()

    async def _execute_app_and_capture_response(
        self, scope: Any, receive: Any
    ) -> Response:
        response_status = 200
        response_headers: list[tuple[bytes, bytes]] = []
        response_body = b""

        async def send(message: dict[str, Any]) -> None:
            nonlocal response_status, response_headers, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message["headers"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")

        await self.app(scope, receive, send)

        return Response(
            content=response_body,
            status_code=response_status,
            headers={
                k.decode("latin-1"): v.decode("latin-1")
                for k, v in response_headers
            },
        )

# Recommended pattern for Moxie: Simple ASGI middleware
class ASGIMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        await self.app(scope, receive, send)

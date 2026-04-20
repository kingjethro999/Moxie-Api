import uuid
from typing import Any

from moxie.middleware.base import ASGIMiddleware


class RequestIDMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        scope["request_id"] = request_id
        
        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append([b"x-request-id", request_id.encode("latin-1")])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

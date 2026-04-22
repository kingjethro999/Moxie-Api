from typing import Any

from moxie.middleware.base import ASGIMiddleware
from moxie.response import Response


class HTTPSRedirectMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope["scheme"] == "https":
            await self.app(scope, receive, send)
            return

        host = dict(scope["headers"]).get(b"host", b"").decode("latin-1")
        path = scope.get("root_path", "") + scope["path"]
        query = scope.get("query_string", b"").decode("latin-1")
        if query:
            path = f"{path}?{query}"
        
        url = f"https://{host}{path}"
        
        response = Response(
            status_code=307,
            headers={"location": url}
        )
        await response(send)

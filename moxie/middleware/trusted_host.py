import re
from typing import Any

from moxie.middleware.base import ASGIMiddleware
from moxie.response import PlainTextResponse


class TrustedHostMiddleware(ASGIMiddleware):
    def __init__(
        self,
        app: Any,
        allowed_hosts: list[str] | None = None,
        www_redirect: bool = True,
    ) -> None:
        super().__init__(app)
        if allowed_hosts is None:
            allowed_hosts = ["*"]
        
        self.allowed_hosts = allowed_hosts
        self.www_redirect = www_redirect
        self.pattern = self._build_pattern(allowed_hosts)

    def _build_pattern(self, allowed_hosts: list[str]) -> re.Pattern:
        patterns = []
        for host in allowed_hosts:
            if host == "*":
                patterns.append(".*")
            elif host.startswith("*."):
                patterns.append(re.escape(host[2:]) + "$")
                patterns.append(r".*\." + re.escape(host[2:]) + "$")
            else:
                patterns.append(re.escape(host) + "$")
        
        return re.compile("|".join(patterns), re.IGNORECASE)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin-1").split(":")[0]

        if not host:
            response = PlainTextResponse("Invalid Host Header", status_code=400)
            await response(send)
            return

        if not self.pattern.match(host):
            response = PlainTextResponse("Disallowed Host", status_code=400)
            await response(send)
            return

        await self.app(scope, receive, send)

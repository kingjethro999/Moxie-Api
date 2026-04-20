from typing import Any, Protocol, runtime_checkable

from moxie.request import Request


@runtime_checkable
class Guard(Protocol):
    scheme_name: str
    openapi_security_scheme: dict[str, Any]

    async def check(self, request: Request) -> None:
        """Raise HTTPException to deny. Return None to allow."""
        ...

class BaseGuard:
    scheme_name: str = "Base"
    openapi_security_scheme: dict[str, Any] = {}

    async def check(self, request: Request) -> None:
        pass

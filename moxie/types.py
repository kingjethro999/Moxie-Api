from typing import Any, Awaitable, Callable, Dict, MutableMapping, Protocol, TypeAlias, Union

Scope: TypeAlias = MutableMapping[str, Any]
Message: TypeAlias = MutableMapping[str, Any]
Receive: TypeAlias = Callable[[], Awaitable[Message]]
Send: TypeAlias = Callable[[Message], Awaitable[None]]
ASGIApp: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]

class RequestHandler(Protocol):
    async def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

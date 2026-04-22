from collections.abc import Callable
from typing import Any


class Dependency:
    def __init__(self, dependency: Callable[..., Any], use_cache: bool = True) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

def Depends(dependency: Callable[..., Any], *, use_cache: bool = True) -> Any:
    return Dependency(dependency, use_cache=use_cache)


class ParamMarker:
    def __init__(self, default: Any = None, alias: str | None = None) -> None:
        self.default = default
        self.alias = alias

class Query(ParamMarker):
    pass

class Header(ParamMarker):
    pass

class Cookie(ParamMarker):
    pass

class Body(ParamMarker):
    pass

class Path(ParamMarker):
    pass

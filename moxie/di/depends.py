from typing import Any, Callable, Optional

class Dependency:
    def __init__(self, dependency: Callable[..., Any], use_cache: bool = True) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

def Depends(dependency: Callable[..., Any], *, use_cache: bool = True) -> Any:
    return Dependency(dependency, use_cache=use_cache)

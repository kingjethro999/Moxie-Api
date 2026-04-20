import inspect
from collections.abc import Callable
from typing import Any

from moxie.di.depends import Dependency


class DependencyContainer:
    def __init__(self) -> None:
        self.singleton_cache: dict[Callable[..., Any], Any] = {}

    async def resolve(
        self,
        dependency_callable: Callable[..., Any],
        request_cache: dict[Callable[..., Any], Any],
        path_params: dict[str, Any],
        request: Any,
    ) -> Any:
        # Check if it's already in request cache
        if dependency_callable in request_cache:
            return request_cache[dependency_callable]
        
        # Check if it's in singleton cache (simplified logic for now)
        if dependency_callable in self.singleton_cache:
            return self.singleton_cache[dependency_callable]

        # Inspect the callable
        sig = inspect.signature(dependency_callable)
        values: dict[str, Any] = {}

        for name, param in sig.parameters.items():
            # Handle special types first
            if param.annotation is type(request): # Check if it's a Request
                values[name] = request
                continue
            
            # Handle path params
            if name in path_params:
                values[name] = path_params[name]
                continue

            # Handle Depends() default values
            if isinstance(param.default, Dependency):
                dep_marker = param.default
                values[name] = await self.resolve(
                    dep_marker.dependency, request_cache, path_params, request
                )
                continue
            
            # Handle type-hint based injection (if annotation is a callable/class)
            # This is a bit advanced, but useful for things like Database classes
            # For now, we only support explicit Depends() or special types

        if inspect.iscoroutinefunction(dependency_callable):
            result = await dependency_callable(**values)
        else:
            result = dependency_callable(**values)

        # Cache the result if needed
        # (For now, we treat everything as request-scoped by default)
        request_cache[dependency_callable] = result
        
        return result

class DependencyResolver:
    def __init__(self, container: DependencyContainer) -> None:
        self.container = container

    async def resolve_handler_deps(
        self,
        handler: Callable[..., Any],
        request: Any,
        path_params: dict[str, Any],
    ) -> dict[str, Any]:
        sig = inspect.signature(handler)
        resolved_values: dict[str, Any] = {}
        request_cache: dict[Callable[..., Any], Any] = {}

        for name, param in sig.parameters.items():
            if name in path_params:
                resolved_values[name] = path_params[name]
            elif isinstance(param.default, Dependency):
                resolved_values[name] = await self.container.resolve(
                    param.default.dependency, request_cache, path_params, request
                )
            elif param.annotation is type(request):
                resolved_values[name] = request
            # Add more inference logic here later (e.g. Query, Body)

        return resolved_values

import inspect
from collections.abc import Callable
from typing import Any

from moxie.background import BackgroundTasks
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
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, Any]:
        from pydantic import BaseModel

        from moxie.di.depends import Body, Header, ParamMarker, Query

        sig = inspect.signature(handler)
        resolved_values: dict[str, Any] = {}
        request_cache: dict[Callable[..., Any], Any] = {}

        for name, param in sig.parameters.items():
            annotation = param.annotation
            default = param.default

            # 1. Special types
            if annotation is type(request):
                resolved_values[name] = request
                continue
            if annotation is BackgroundTasks:
                resolved_values[name] = background_tasks
                continue

            # 2. Explicit Dependencies
            if isinstance(default, Dependency):
                resolved_values[name] = await self.container.resolve(
                    default.dependency, request_cache, path_params, request
                )
                continue

            # 3. Path Parameters
            if name in path_params:
                resolved_values[name] = path_params[name]
                continue

            # 4. Explicit Markers (Query, Header, etc.)
            if isinstance(default, ParamMarker):
                param_name = default.alias or name
                if isinstance(default, Query):
                    resolved_values[name] = request.query_params.get(
                        param_name, default.default
                    )
                elif isinstance(default, Header):
                    resolved_values[name] = request.headers.get(
                        param_name.lower(), default.default
                    )
                elif isinstance(default, Body):
                    body_json = await request.json()
                    is_pydantic = (
                        inspect.isclass(annotation) and 
                        issubclass(annotation, BaseModel)
                    )
                    if is_pydantic:
                        resolved_values[name] = annotation.model_validate(body_json)
                    else:
                        resolved_values[name] = body_json
                continue

            # 5. Implicit Inference
            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                # Infer as Body
                body_json = await request.json()
                resolved_values[name] = annotation.model_validate(body_json)
                continue
            
            # Default to Query if simple type and not in path
            is_simple_type = (
                annotation in (str, int, float, bool, None) or 
                annotation is inspect.Parameter.empty
            )
            if is_simple_type:
                resolved_values[name] = request.query_params.get(name)
                if (
                    resolved_values[name] is None and 
                    default is not inspect.Parameter.empty
                ):
                    resolved_values[name] = default

        return resolved_values

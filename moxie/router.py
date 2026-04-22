from collections.abc import Callable
from typing import Any

from moxie.guards.base import Guard
from moxie.routing.matcher import CompiledRouter


class Route:
    __slots__ = (
        "path", 
        "methods", 
        "handler", 
        "name", 
        "tags", 
        "guards",
        "summary",
        "description",
        "operation_id",
        "deprecated",
        "include_in_schema",
        "responses",
        "is_asgi",
    )
    
    def __init__(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: list[str],
        name: str | None = None,
        tags: list[str] | None = None,
        guards: list[Guard] | None = None,
        summary: str | None = None,
        description: str | None = None,
        operation_id: str | None = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
        responses: dict[int | str, dict[str, Any]] | None = None,
    ) -> None:
        self.path = path
        self.handler = handler
        self.methods = methods
        self.name = name or handler.__name__
        self.tags = tags or []
        self.guards = guards or []
        self.summary = summary
        self.description = description
        self.operation_id = operation_id or self.name
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema
        self.responses = responses or {}
        self.is_asgi = False

class ASGIRoute(Route):
    def __init__(self, path: str, app: Any, name: str | None = None) -> None:
        super().__init__(
            path, 
            handler=app, 
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"], 
            name=name or "asgi_app",
            include_in_schema=False
        )
        self.is_asgi = True

class WebSocketRoute(Route):
    def __init__(
        self,
        path: str,
        handler: Callable[..., Any],
        name: str | None = None,
        tags: list[str] | None = None,
        guards: list[Guard] | None = None,
    ) -> None:
        super().__init__(
            path, 
            handler, 
            methods=["WS"], 
            name=name, 
            tags=tags, 
            guards=guards,
            include_in_schema=True
        )

class Router:
    def __init__(self, prefix: str = "", guards: list[Guard] | None = None) -> None:
        self.prefix = prefix
        self.routes: list[Route | WebSocketRoute] = []
        self.guards = guards or []
        self._compiled_router: CompiledRouter | None = None

    def add_route(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: list[str],
        name: str | None = None,
        tags: list[str] | None = None,
        guards: list[Guard] | None = None,
        **openapi_kwargs: Any,
    ) -> None:
        full_path = self.prefix + path
        all_guards = self.guards + (guards or [])
        
        route = Route(
            full_path, 
            handler, 
            [m.upper() for m in methods], 
            name=name, 
            tags=tags, 
            guards=all_guards,
            **openapi_kwargs
        )
        self.routes.append(route)
        self._compiled_router = None

    def add_ws_route(
        self,
        path: str,
        handler: Callable[..., Any],
        name: str | None = None,
        tags: list[str] | None = None,
        guards: list[Guard] | None = None,
    ) -> None:
        full_path = self.prefix + path
        all_guards = self.guards + (guards or [])
        self.routes.append(WebSocketRoute(full_path, handler, name, tags, all_guards))
        self._compiled_router = None

    def ws(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            self.add_ws_route(path, handler, **kwargs)
            return handler
        return decorator

    def get(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["GET"], **kwargs)

    def post(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["POST"], **kwargs)

    def put(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["PUT"], **kwargs)

    def delete(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["DELETE"], **kwargs)

    def patch(
        self, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["PATCH"], **kwargs)

    def _add_method_route(
        self, path: str, methods: list[str], **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(path, handler, methods, **kwargs)
            return handler
        return decorator

    def mount(self, router: "Router") -> None:
        for route in router.routes:
            # Create a copy or update path to include current prefix
            # Note: we update the path of the route object itself here
            # but since Router.mount is usually called during setup, this is
            # mostly fine.
            # In a more robust version, we'd clone the route object.
            if self.prefix and not route.path.startswith(self.prefix):
                route.path = self.prefix + route.path
            self.routes.append(route)
            self._compiled_router = None

    def mount_asgi(self, path: str, app: Any, name: str | None = None) -> None:
        if not path.endswith("/") and path != "":
            path += "/"
        
        full_path = self.prefix + path
        # Use a wildcard match for ASGI mounts if the matcher supports it
        # or we just match the prefix in the resolver.
        # For now, let's assume we want to match the prefix.
        self.routes.append(ASGIRoute(full_path, app, name))
        self._compiled_router = None

    @property
    def compiled_router(self) -> CompiledRouter:
        if self._compiled_router is None:
            self._compiled_router = CompiledRouter()
            for route in self.routes:
                self._compiled_router.add_route(route)
        return self._compiled_router

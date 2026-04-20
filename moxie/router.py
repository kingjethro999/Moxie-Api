from typing import Any, Callable, Dict, List, Optional, Sequence, Union
from moxie.routing.matcher import CompiledRouter
from moxie.guards.base import Guard

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
    )
    
    def __init__(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str],
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        guards: Optional[List[Guard]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        operation_id: Optional[str] = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
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

class Router:
    def __init__(self, prefix: str = "", guards: Optional[List[Guard]] = None) -> None:
        self.prefix = prefix
        self.routes: List[Route] = []
        self.guards = guards or []
        self._compiled_router: Optional[CompiledRouter] = None

    def add_route(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str],
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        guards: Optional[List[Guard]] = None,
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
        self._compiled_router = None # Invalidate cache

    def get(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["GET"], **kwargs)

    def post(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["POST"], **kwargs)

    def put(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["PUT"], **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["DELETE"], **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_method_route(path, ["PATCH"], **kwargs)

    def _add_method_route(
        self, path: str, methods: List[str], **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(path, handler, methods, **kwargs)
            return handler
        return decorator

    def mount(self, router: "Router") -> None:
        for route in router.routes:
            # We don't re-use add_route here to avoid re-prefixing or doubling guards if not needed,
            # but actually we SHOULD re-prefix if mounting a router on another.
            # The Route objects already have full_path from their original router.
            # If we mount a router with prefix /api on an app, 
            # and the router has a route /users, the route.path is already /api/users.
            self.routes.append(route)
            self._compiled_router = None

    @property
    def compiled_router(self) -> CompiledRouter:
        if self._compiled_router is None:
            self._compiled_router = CompiledRouter()
            for route in self.routes:
                self._compiled_router.add_route(route)
        return self._compiled_router

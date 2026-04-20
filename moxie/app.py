import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple

from moxie.types import Scope, Receive, Send
from moxie.request import Request, WebSocket
from moxie.response import Response, JSONResponse, PlainTextResponse, HTMLResponse
from moxie.router import Router, Route, WebSocketRoute
from moxie.exceptions import HTTPException
from moxie.di.container import DependencyContainer, DependencyResolver
from moxie.background import BackgroundTasks
from moxie.plugins import Plugin
from moxie.openapi.builder import OpenAPIBuilder
from moxie.openapi.ui import get_swagger_ui_html, get_redoc_html

logger = logging.getLogger("moxie")

class Moxie:
    def __init__(
        self,
        title: str = "Moxie API",
        version: str = "2.0.0",
        description: Optional[str] = None,
        openapi: bool = True,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        openapi_url: Optional[str] = "/openapi.json",
        swagger_ui_parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.title = title
        self.version = version
        self.description = description
        self.router = Router()
        self.di_container = DependencyContainer()
        self.di_resolver = DependencyResolver(self.di_container)
        self.plugins: Dict[str, Plugin] = {}
        self.middleware_defs: List[Tuple[Type[Any], Dict[str, Any]]] = []
        self.asgi_app: Optional[Callable[[Scope, Receive, Send], Any]] = None
        
        self._on_startup: List[Callable[..., Any]] = []
        self._on_shutdown: List[Callable[..., Any]] = []
        self.state: Dict[str, Any] = {}
        
        self.openapi_url = openapi_url
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_parameters = swagger_ui_parameters
        
        if openapi:
            self.openapi_builder = OpenAPIBuilder(self)
            self._setup_openapi_routes()

    def _setup_openapi_routes(self) -> None:
        if self.openapi_url:
            @self.get(self.openapi_url, include_in_schema=False)
            async def openapi() -> Dict[str, Any]:
                return self.openapi_builder.spec
        
        if self.docs_url and self.openapi_url:
            @self.get(self.docs_url, include_in_schema=False)
            async def swagger_ui() -> HTMLResponse:
                return HTMLResponse(
                    get_swagger_ui_html(
                        openapi_url=self.openapi_url,
                        title=f"{self.title} - Swagger UI",
                        swagger_ui_parameters=self.swagger_ui_parameters,
                    )
                )
                
        if self.redoc_url and self.openapi_url:
            @self.get(self.redoc_url, include_in_schema=False)
            async def redoc() -> HTMLResponse:
                return HTMLResponse(
                    get_redoc_html(
                        openapi_url=self.openapi_url,
                        title=f"{self.title} - ReDoc",
                    )
                )

    def add_middleware(self, middleware_class: Type[Any], **kwargs: Any) -> None:
        self.middleware_defs.insert(0, (middleware_class, kwargs))
        self.asgi_app = None

    def get(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.post(path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.put(path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.delete(path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.patch(path, **kwargs)

    def ws(self, path: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.ws(path, **kwargs)

    def install(self, plugin: Plugin) -> None:
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin with name '{plugin.name}' already installed.")
        self.plugins[plugin.name] = plugin

    def mount(self, path: str, app: Any) -> None:
        if isinstance(app, Router):
            prefix_router = Router(prefix=path)
            prefix_router.mount(app)
            self.router.mount(prefix_router)
        else:
            pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.asgi_app is None:
            self.asgi_app = self._build_middleware_stack()

        await self.asgi_app(scope, receive, send)

    def _build_middleware_stack(self) -> Callable[[Scope, Receive, Send], Any]:
        app = self._dispatch
        for middleware_class, kwargs in self.middleware_defs:
            app = middleware_class(app, **kwargs)
        return app

    async def _dispatch(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.handle_lifespan(scope, receive, send)
            return

        if scope["type"] == "http":
            await self.handle_http(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await self.handle_websocket(scope, receive, send)
            return

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    for plugin in self.plugins.values():
                        await plugin.on_startup(self)
                    for handler in self._on_startup:
                        if inspect.iscoroutinefunction(handler):
                            await handler()
                        else:
                            handler()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    logger.error(f"Startup failed: {exc}")
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
            elif message["type"] == "lifespan.shutdown":
                try:
                    for handler in self._on_shutdown:
                        if inspect.iscoroutinefunction(handler):
                            await handler()
                        else:
                            handler()
                    for plugin in self.plugins.values():
                        await plugin.on_shutdown(self)
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as exc:
                    logger.error(f"Shutdown failed: {exc}")
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                break

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        path = scope["path"]
        method = scope["method"]

        resolved = self.router.compiled_router.resolve(path, method)
        if resolved is None:
            response = PlainTextResponse("Not Found", status_code=404)
            await response(send)
            return

        route, path_params = resolved
        try:
            for guard in route.guards:
                await guard.check(request)

            background_tasks = BackgroundTasks()
            kwargs = await self.di_resolver.resolve_handler_deps(route.handler, request, path_params)
            sig = inspect.signature(route.handler)
            for name, param in sig.parameters.items():
                if param.annotation is BackgroundTasks:
                    kwargs[name] = background_tasks

            if inspect.iscoroutinefunction(route.handler):
                response_data = await route.handler(**kwargs)
            else:
                response_data = route.handler(**kwargs)

            if isinstance(response_data, Response):
                response = response_data
            elif isinstance(response_data, (dict, list)):
                response = JSONResponse(response_data)
            else:
                response = Response(response_data)

            await response(send)
            await background_tasks.run()

        except HTTPException as exc:
            response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
            if exc.headers:
                response.headers.update(exc.headers)
            await response(send)
        except Exception as exc:
            logger.exception("Internal Server Error")
            response = PlainTextResponse(f"Internal Server Error", status_code=500)
            await response(send)

    async def handle_websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        ws = WebSocket(scope, receive, send)
        path = scope["path"]
        
        resolved = self.router.compiled_router.resolve(path, "WS")
        if resolved is None:
            await ws.close(code=1006)
            return

        route, path_params = resolved
        try:
            for guard in route.guards:
                await guard.check(ws) # type: ignore (Guards handle Request or WebSocket)

            kwargs = await self.di_resolver.resolve_handler_deps(route.handler, ws, path_params)
            sig = inspect.signature(route.handler)
            for name, param in sig.parameters.items():
                if param.annotation is WebSocket:
                    kwargs[name] = ws

            if inspect.iscoroutinefunction(route.handler):
                await route.handler(**kwargs)
            else:
                route.handler(**kwargs)

        except Exception as exc:
            logger.exception("WebSocket Error")
            await ws.close(code=1011)

    def on_startup(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        self._on_startup.append(handler)
        return handler

    def on_shutdown(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        self._on_shutdown.append(handler)
        return handler

    def openapi(self) -> Dict[str, Any]:
        return self.openapi_builder.spec

# CLAUDE.md — Moxie v2

> This file supersedes `CLAUDE.md` (v1). It is the single authoritative reference for all AI assistants
> and human contributors working on Moxie v2. Read every section before writing code.

---

## What Changed in v2

| Area | v1 | v2 |
|---|---|---|
| OpenAPI | Not supported | Auto-generated from type hints & decorators |
| Docs UI | None | Built-in Swagger UI + ReDoc at `/docs` and `/redoc` |
| WebSockets | Lifecycle only | First-class `@app.ws()` handler with typed messages |
| Validation | Optional pydantic | Pydantic v2 required for validated routes; raw routes still zero-dep |
| Plugins | None | Official plugin protocol + plugin registry |
| Background Tasks | None | `BackgroundTasks` injected via DI |
| Rate Limiting | None | `@app.limit()` decorator backed by sliding-window token bucket |
| Guards | None | `@app.guard()` — composable auth/permission layer |
| Event Hooks | `lifespan` only | `on_startup`, `on_shutdown`, `on_request`, `on_response` hooks |
| CLI | None | `moxie dev`, `moxie routes`, `moxie openapi export` |
| HTTP/2 | No | Yes — via `hypercorn` with H2 push support |
| Server-Sent Events | No | First-class `EventSourceResponse` |
| Health & Observability | No | Built-in `/healthz`, `/readyz`, structured request logging |

---

## Project Identity

**Name:** Moxie
**Version:** 2.0
**Tagline:** The Python web framework that gets out of your way — and documents itself.
**Language:** Python 3.11+
**License:** MIT

Moxie v2 is a ground-up ASGI web framework. Zero dependency on FastAPI, Starlette, or Django. Every system is written and owned by this project.

The defining feature of v2 is **zero-annotation-overhead OpenAPI** — Moxie reads your existing Python type hints and generates a full OpenAPI 3.1 spec automatically. No decorating your models with special classes. No manual schema registration. Write idiomatic Python; get professional API docs for free.

---

## Vision & Goals (v2)

1. **Self-documenting by default** — OpenAPI 3.1 generated from type hints at zero extra cost to the developer.
2. **Fast by default** — async-first, trie-based routing, zero-copy response streaming, `__slots__` on hot objects.
3. **Honest about its opinions** — Moxie makes choices (pydantic for schemas, anyio for concurrency) and owns them.
4. **Composable at every layer** — routers, middleware, guards, plugins, and apps are all mountable objects.
5. **Observable out of the box** — structured logging, health endpoints, and trace-id propagation included in core.
6. **Developer-experience first** — the CLI, the error messages, and the interactive docs exist to remove friction.

---

## Repository Layout (v2)

```
moxie/
├── moxie/
│   ├── __init__.py                  # Public re-exports — everything a user needs in one place
│   ├── app.py                       # Moxie application class + lifespan management
│   ├── router.py                    # Router, Route, WebSocketRoute, Mount
│   ├── request.py                   # Request (HTTP) + WebSocketConnection
│   ├── response.py                  # Response hierarchy + EventSourceResponse
│   │
│   ├── routing/
│   │   ├── converters.py            # Path parameter type converters
│   │   ├── matcher.py               # Compiled trie URL matcher
│   │   └── operations.py            # RouteOperation — metadata for OpenAPI
│   │
│   ├── openapi/                     # ★ New in v2
│   │   ├── __init__.py
│   │   ├── builder.py               # Walks all routes, builds OpenAPI dict
│   │   ├── schema.py                # Python type → JSON Schema conversion
│   │   ├── extractor.py             # Extracts params from handler signatures
│   │   ├── ui.py                    # Serves Swagger UI + ReDoc HTML
│   │   └── models.py                # Internal OpenAPI object models (Info, Path, Op, etc.)
│   │
│   ├── middleware/
│   │   ├── base.py
│   │   ├── cors.py
│   │   ├── gzip.py
│   │   ├── trustedhost.py
│   │   ├── ratelimit.py             # ★ New in v2 — sliding window token bucket
│   │   ├── requestid.py             # ★ New in v2 — X-Request-ID propagation
│   │   └── logging.py              # ★ New in v2 — structured request logging
│   │
│   ├── di/
│   │   ├── container.py
│   │   └── depends.py
│   │
│   ├── guards/                      # ★ New in v2
│   │   ├── base.py                  # Guard protocol
│   │   └── bearer.py                # BearerTokenGuard convenience class
│   │
│   ├── background.py                # ★ New in v2 — BackgroundTasks
│   ├── plugins.py                   # ★ New in v2 — Plugin protocol + registry
│   ├── health.py                    # ★ New in v2 — /healthz + /readyz handlers
│   ├── exceptions.py
│   ├── types.py
│   └── utils/
│       ├── concurrency.py
│       ├── encoding.py
│       └── inspect.py               # ★ New in v2 — deep signature/annotation utils
│
├── moxie_cli/                       # ★ New in v2 — standalone CLI package
│   ├── __init__.py
│   ├── main.py                      # Entry point: `moxie`
│   ├── commands/
│   │   ├── dev.py                   # `moxie dev` — hot-reload dev server
│   │   ├── routes.py                # `moxie routes` — table of all routes
│   │   └── openapi.py               # `moxie openapi export` — dump spec to JSON/YAML
│
├── tests/
│   ├── conftest.py
│   ├── test_routing.py
│   ├── test_middleware.py
│   ├── test_di.py
│   ├── test_request.py
│   ├── test_response.py
│   ├── test_openapi/                # ★ New in v2
│   │   ├── test_builder.py
│   │   ├── test_schema.py
│   │   └── test_extractor.py
│   ├── test_guards.py               # ★ New in v2
│   ├── test_background.py           # ★ New in v2
│   └── test_plugins.py              # ★ New in v2
│
├── benchmarks/
├── docs/
├── examples/
│   ├── hello.py
│   ├── crud_api.py                  # Full CRUD with OpenAPI docs example
│   ├── websockets.py
│   └── plugin_example.py
├── pyproject.toml
├── CHANGELOG.md
├── CLAUDE.md                        # v1 reference (kept for history)
└── CLAUDE.v2.md                     # This file
```

---

## Architecture Overview

### ASGI Lifecycle (unchanged from v1)

```
ASGI server (uvicorn / hypercorn)
  └── Moxie.__call__(scope, receive, send)
        ├── scope == "lifespan" → LifespanManager
        ├── scope == "websocket" → WebSocketRouter
        └── scope == "http"
              └── MiddlewareStack.dispatch(request)
                    └── GuardChain.check(request)
                          └── Router.resolve(path, method)
                                └── DependencyResolver.resolve(handler)
                                      └── handler(**deps) → Response
                                            └── BackgroundTaskRunner.run()
                                                  └── Response.send(send)
```

### Extended Lifecycle (v2 additions)

```
App startup:
  ├── Plugin.on_startup() for each plugin
  ├── on_startup hooks (user-defined)
  └── OpenAPIBuilder.build() → cached spec

Per request:
  ├── RequestIDMiddleware injects X-Request-ID
  ├── StructuredLoggingMiddleware opens log record
  ├── RateLimitMiddleware checks token bucket
  ├── GuardChain evaluates guards (short-circuit on deny)
  ├── Handler executes
  ├── BackgroundTasks enqueued
  └── StructuredLoggingMiddleware closes log record (duration, status)

App shutdown:
  ├── BackgroundTaskRunner drains queue
  ├── on_shutdown hooks (user-defined)
  └── Plugin.on_shutdown() for each plugin
```

---

## ★ OpenAPI v2 — Full Specification

This is the most important new system in v2. Read this section completely before touching anything in `moxie/openapi/`.

### Design Principle

Moxie generates OpenAPI docs **entirely from Python source** — type annotations, docstrings, and decorator parameters. The developer writes zero OpenAPI-specific code for the common case. Every annotation and docstring the developer already writes becomes documentation.

```python
from moxie import Moxie
from pydantic import BaseModel

app = Moxie(title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True

@app.post("/items", tags=["items"], summary="Create an item")
async def create_item(body: Item) -> Item:
    """
    Create a new item in the catalogue.

    Returns the created item with all fields populated.
    """
    return body
```

This alone produces a fully valid OpenAPI 3.1 document, served at `/openapi.json`, with interactive docs at `/docs` (Swagger UI) and `/redoc`.

---

### OpenAPI Builder (`moxie/openapi/builder.py`)

`OpenAPIBuilder` is instantiated once at app startup. It is called after all routes are registered.

**Responsibilities:**
- Walk every `Route` and `WebSocketRoute` registered on the app (including mounted sub-routers).
- For each route, call `OperationExtractor.extract(route)` to produce an `Operation` object.
- Assemble all operations into a `paths` dict.
- Call `SchemaBuilder.collect()` to gather all referenced models and produce a `components/schemas` dict.
- Output a single Python `dict` conforming to OpenAPI 3.1.0.
- Cache the result. Invalidated only if routes change (dev mode) or `app.rebuild_openapi()` is called.

**Class interface:**

```python
class OpenAPIBuilder:
    def __init__(self, app: "Moxie") -> None: ...

    def build(self) -> dict:
        """Build and return the full OpenAPI 3.1 document as a dict."""

    def invalidate(self) -> None:
        """Clear the cache — forces rebuild on next access."""

    @property
    def spec(self) -> dict:
        """Cached spec. Calls build() on first access."""
```

**Output structure:**

```python
{
    "openapi": "3.1.0",
    "info": {
        "title": app.title,
        "version": app.version,
        "description": app.description or "",
    },
    "paths": { ... },           # populated from routes
    "components": {
        "schemas": { ... },     # all pydantic models + dataclasses
        "securitySchemes": { ... },  # populated from guards
    },
    "tags": [ ... ],            # collected from route `tags` params
}
```

---

### Schema Builder (`moxie/openapi/schema.py`)

Converts Python types to JSON Schema objects. This is the core intellectual work of the OpenAPI system.

**Type mapping rules:**

| Python Type | JSON Schema |
|---|---|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `bytes` | `{"type": "string", "format": "binary"}` |
| `datetime.datetime` | `{"type": "string", "format": "date-time"}` |
| `datetime.date` | `{"type": "string", "format": "date"}` |
| `uuid.UUID` | `{"type": "string", "format": "uuid"}` |
| `None` / `type(None)` | `{"type": "null"}` |
| `list[T]` | `{"type": "array", "items": <schema for T>}` |
| `dict[str, V]` | `{"type": "object", "additionalProperties": <schema for V>}` |
| `tuple[A, B]` | `{"type": "array", "prefixItems": [...], "minItems": 2, "maxItems": 2}` |
| `T \| None` (`Optional[T]`) | `{"anyOf": [<schema for T>, {"type": "null"}]}` |
| `Union[A, B]` | `{"anyOf": [<schema for A>, <schema for B>]}` |
| `Literal["a", "b"]` | `{"enum": ["a", "b"]}` |
| `pydantic.BaseModel` subclass | `{"$ref": "#/components/schemas/<ClassName>"}` |
| `dataclass` | `{"$ref": "#/components/schemas/<ClassName>"}` |
| `TypedDict` | Inlined object schema |
| `Annotated[T, ...]` | Schema for `T`, merged with any `pydantic.Field` constraints |

**Pydantic model expansion:**

When a `BaseModel` subclass is encountered, `SchemaBuilder` calls `model.model_json_schema()` (Pydantic v2) and registers the result under `components/schemas`. References use `$ref`. Circular references are detected and resolved via `$defs`.

**Dataclass expansion:**

Dataclasses are converted field-by-field using `dataclasses.fields()`. Each field's `type` annotation is recursively converted. Default values are included as `default` in the schema. `field(metadata={"description": "..."})` populates the field's `description`.

**Key functions:**

```python
def python_type_to_schema(tp: type, schema_collector: SchemaCollector) -> dict:
    """
    Convert a Python type annotation to a JSON Schema dict.
    Registers any named models into schema_collector.
    Never raises — returns {"type": "object"} as fallback for unknown types
    and emits a warning.
    """

def collect_model_schemas(collector: SchemaCollector) -> dict[str, dict]:
    """
    Return all collected named schemas as a components/schemas dict.
    Called once by OpenAPIBuilder after all routes are processed.
    """
```

---

### Operation Extractor (`moxie/openapi/extractor.py`)

Extracts OpenAPI `Operation` objects from a `Route` by inspecting the handler's signature, return annotation, and decorator parameters.

**Parameter sources and their OpenAPI location:**

| Source | OpenAPI `in` | How detected |
|---|---|---|
| Path `{name}` segment | `path` | Name present in route pattern |
| Function param not in path, not `Request`, not `Depends`, primitive type | `query` | Default |
| Function param annotated `Header[T]` | `header` | Wrapper type |
| Function param annotated `Cookie[T]` | `cookie` | Wrapper type |
| Function param is `BaseModel` or `dataclass` and method is POST/PUT/PATCH | `requestBody` | Body inference |
| Function param is `UploadFile` or `list[UploadFile]` | `requestBody` multipart | Type check |

**Docstring parsing:**

The handler's docstring is parsed as follows:
- First paragraph → operation `description`.
- Google-style `Args:` section → per-parameter descriptions (merged into parameter schema).
- Google-style `Returns:` section → response description.
- Google-style `Raises:` section → generates additional `responses` entries (e.g. `HTTPException(404)` → `404` response).

```python
async def get_user(user_id: int) -> User:
    """
    Fetch a user by their numeric ID.

    Args:
        user_id: The unique integer ID of the user.

    Returns:
        The full User object.

    Raises:
        HTTPException(404): User not found.
        HTTPException(403): Insufficient permissions.
    """
```

Produces:
- `description`: "Fetch a user by their numeric ID."
- `parameters[user_id].description`: "The unique integer ID of the user."
- `responses.200.description`: "The full User object."
- `responses.404`: included with description "User not found."
- `responses.403`: included with description "Insufficient permissions."

**Return type → response schema:**

The function's return annotation is converted by `SchemaBuilder` and placed under `responses.200.content["application/json"].schema`. Special cases:

- `None` / no annotation → `204 No Content` response, no body.
- `Response` subclass → raw response, no schema inferred.
- `StreamingResponse` → `200` with `application/octet-stream`.
- `EventSourceResponse` → `200` with `text/event-stream`.

**Decorator parameters** (all optional, all passed as kwargs to route decorators):

```python
@app.get(
    "/items/{item_id}",
    summary="Get an item",          # Short one-line description (overrides docstring first line)
    description="Long description", # Overrides full docstring body
    tags=["items"],                 # OpenAPI tags for grouping
    operation_id="getItem",         # Explicit operationId (auto-generated if omitted)
    deprecated=True,                # Marks operation as deprecated
    include_in_schema=False,        # Exclude from OpenAPI output entirely
    responses={                     # Additional response codes
        404: {"description": "Item not found"},
        422: {"description": "Validation error"},
    },
)
```

---

### OpenAPI UI (`moxie/openapi/ui.py`)

Two UIs are served automatically when `openapi=True` (default) in `Moxie()`:

| URL | UI | Notes |
|---|---|---|
| `/openapi.json` | Raw spec | Always JSON, regardless of `Accept` header |
| `/docs` | Swagger UI | Default; embedded via CDN, configurable |
| `/redoc` | ReDoc | More readable; good for external consumers |

Both UI pages are served as inline HTML strings (no static file server dependency). CDN assets are fetched by the browser, not Moxie.

**Configuration:**

```python
app = Moxie(
    title="My API",
    version="2.0.0",
    description="Full description, supports **Markdown**.",
    openapi=True,               # Enable (default True)
    docs_url="/docs",           # Swagger UI path (set None to disable)
    redoc_url="/redoc",         # ReDoc path (set None to disable)
    openapi_url="/openapi.json",# Spec URL (set None to disable all)
    swagger_ui_parameters={     # Passed to SwaggerUIBundle config
        "deepLinking": True,
        "displayRequestDuration": True,
    },
)
```

**Disabling docs in production:**

```python
import os
app = Moxie(
    docs_url=None if os.getenv("ENV") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV") == "production" else "/redoc",
)
```

---

### OpenAPI + Guards (Security Schemes)

When a Guard is applied to a route, the OpenAPI builder automatically adds a `securitySchemes` entry and a `security` requirement to the affected operation.

```python
from moxie.guards import BearerTokenGuard

auth = BearerTokenGuard(scheme_name="BearerAuth")

@app.get("/me", guards=[auth])
async def get_me(user: CurrentUser) -> User:
    ...
```

Produces in the spec:

```json
{
  "components": {
    "securitySchemes": {
      "BearerAuth": { "type": "http", "scheme": "bearer" }
    }
  },
  "paths": {
    "/me": {
      "get": {
        "security": [{ "BearerAuth": [] }]
      }
    }
  }
}
```

Custom guards must implement:

```python
class Guard(Protocol):
    scheme_name: str
    openapi_security_scheme: dict  # The securityScheme dict to register

    async def check(self, request: Request) -> None:
        """Raise HTTPException to deny. Return None to allow."""
```

---

### `moxie openapi export` CLI

```bash
# Export to stdout as JSON
moxie openapi export myapp:app

# Export to file
moxie openapi export myapp:app --output openapi.json

# Export as YAML
moxie openapi export myapp:app --format yaml --output openapi.yaml

# Validate the spec against OpenAPI 3.1 schema
moxie openapi validate openapi.json
```

The `export` command imports the app object, calls `app.openapi()`, and serialises without starting the server. Safe to run in CI.

---

## ★ WebSockets (v2)

First-class WebSocket handler with typed message contracts.

```python
from moxie import Moxie
from moxie.websocket import WebSocket
from pydantic import BaseModel

app = Moxie()

class ChatMessage(BaseModel):
    user: str
    text: str

@app.ws("/chat/{room_id}")
async def chat(ws: WebSocket, room_id: str) -> None:
    await ws.accept()
    async for msg in ws.iter_json(ChatMessage):
        await ws.send_json({"echo": msg.text})
    await ws.close()
```

`WebSocket` methods:
- `await ws.accept(subprotocol=None)`
- `await ws.receive_text() -> str`
- `await ws.receive_bytes() -> bytes`
- `await ws.receive_json(model: type[T]) -> T` — validates via pydantic
- `async for msg in ws.iter_json(Model)` — typed message stream
- `await ws.send_text(data: str)`
- `await ws.send_bytes(data: bytes)`
- `await ws.send_json(data: dict | BaseModel)`
- `await ws.close(code=1000)`
- `ws.state` — arbitrary per-connection state bag

WebSocket routes appear in the OpenAPI spec under their path with a note that they use the WebSocket protocol. Full AsyncAPI generation is planned for v3.

---

## ★ Background Tasks (v2)

Injected via DI. Tasks run after the response is sent — the client does not wait.

```python
from moxie import Moxie
from moxie.background import BackgroundTasks

app = Moxie()

async def send_welcome_email(email: str) -> None:
    ...  # slow I/O

@app.post("/register")
async def register(body: RegisterBody, tasks: BackgroundTasks) -> dict:
    tasks.add(send_welcome_email, body.email)
    return {"status": "registered"}
```

`BackgroundTasks.add(func, *args, **kwargs)` — enqueues one task. Tasks are run in order, sequentially, after the response bytes are flushed. Exceptions in background tasks are logged but do not affect the response.

For parallel background work use `tasks.add_concurrent([...])`.

---

## ★ Guards (v2)

Guards are async callables that run before the handler. They either pass silently or raise `HTTPException`.

```python
from moxie.guards import Guard
from moxie import Request, HTTPException

class AdminOnly(Guard):
    scheme_name = "AdminBearer"
    openapi_security_scheme = {"type": "http", "scheme": "bearer"}

    async def check(self, request: Request) -> None:
        token = request.headers.get("Authorization", "")
        if not token.startswith("Bearer admin-"):
            raise HTTPException(403, "Admin access required")

admin = AdminOnly()

@app.delete("/users/{user_id}", guards=[admin])
async def delete_user(user_id: int) -> None:
    ...
```

Guards compose — `guards=[auth, admin]` means both must pass (AND logic). For OR logic, create a `AnyGuard([auth, admin])` combinator.

Router-level guards apply to all routes on that router:

```python
admin_router = Router(prefix="/admin", guards=[admin])
app.mount(admin_router)
```

---

## ★ Plugins (v2)

Plugins extend the app without monkey-patching. They hook into startup/shutdown and can register routes, middleware, and DI providers.

```python
from moxie.plugins import Plugin

class DatabasePlugin(Plugin):
    name = "database"

    def __init__(self, url: str) -> None:
        self.url = url
        self.pool = None

    async def on_startup(self, app: "Moxie") -> None:
        self.pool = await create_pool(self.url)
        app.state.db = self.pool

    async def on_shutdown(self, app: "Moxie") -> None:
        await self.pool.close()

app = Moxie()
app.install(DatabasePlugin(url="postgresql://..."))
```

Plugin rules:
- Every plugin must have a unique `name: str` class attribute.
- Plugins must not register routes with overlapping paths.
- Plugins must not mutate `app.state` after startup.
- `on_startup` and `on_shutdown` are both optional.

---

## ★ Rate Limiting (v2)

```python
from moxie.middleware import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    limit=100,          # requests
    window=60,          # seconds
    key_func=lambda r: r.client.host,  # default: by IP
)
```

Per-route overrides via decorator:

```python
@app.get("/search")
@app.limit(requests=10, window=1)   # 10 req/sec on this route only
async def search(q: str) -> list:
    ...
```

When the limit is exceeded, Moxie returns `429 Too Many Requests` with `Retry-After` header. The token bucket state is stored in-process (default) or in Redis via `RedisRateLimitBackend`.

---

## ★ Server-Sent Events (v2)

```python
from moxie.response import EventSourceResponse
import asyncio

@app.get("/stream")
async def stream() -> EventSourceResponse:
    async def generator():
        for i in range(10):
            yield {"data": f"chunk {i}", "event": "update"}
            await asyncio.sleep(0.5)

    return EventSourceResponse(generator())
```

`EventSourceResponse` handles:
- `data:` field serialisation (auto-JSON if dict, raw string if str)
- `event:` field (optional)
- `id:` field (optional)
- `retry:` field (optional)
- Ping keepalive every 15 seconds (configurable)

---

## ★ Health & Observability (v2)

```python
from moxie.health import HealthPlugin

app.install(HealthPlugin(
    checks=[
        DatabaseCheck(lambda: app.state.db),
        RedisCheck(lambda: app.state.redis),
    ]
))
```

This registers:
- `GET /healthz` — liveness. Returns `200 {"status": "ok"}` always (process is alive).
- `GET /readyz` — readiness. Runs all checks. Returns `200` if all pass, `503` if any fail.

Both endpoints are excluded from OpenAPI output by default (`include_in_schema=False`).

**Structured logging** (via `StructuredLoggingMiddleware`) emits one JSON log line per request:

```json
{
  "timestamp": "2025-04-20T10:00:00Z",
  "request_id": "abc-123",
  "method": "GET",
  "path": "/items/42",
  "status": 200,
  "duration_ms": 4.2,
  "client_ip": "1.2.3.4"
}
```

---

## ★ CLI (v2)

Installed as the `moxie` command via `moxie-cli` package.

```bash
# Start dev server with hot reload
moxie dev myapp:app --port 8000 --reload

# Print all registered routes as a table
moxie routes myapp:app

# Export OpenAPI spec
moxie openapi export myapp:app --output openapi.json
moxie openapi export myapp:app --format yaml

# Validate an OpenAPI spec file
moxie openapi validate openapi.json
```

`moxie routes` output example:

```
METHOD   PATH                    NAME              TAGS
GET      /                       index             []
GET      /items                  list_items        [items]
POST     /items                  create_item       [items]
GET      /items/{item_id:int}    get_item          [items]
DELETE   /items/{item_id:int}    delete_item       [items]
WS       /chat/{room_id}         chat              [ws]
```

---

## Coding Standards (v2 — additions to v1)

### OpenAPI Code Rules

- `OpenAPIBuilder`, `SchemaBuilder`, and `OperationExtractor` must all be **pure functions at their core** — no side effects, no I/O, no mutations. They take data in and return data out.
- The entire OpenAPI spec must be buildable and testable with zero running server (import the builder, give it routes, get a dict back).
- `SchemaBuilder` must never raise on unknown types. Unknown types fall back to `{"type": "object"}` with a logged warning.
- All OpenAPI output keys must follow camelCase per the spec (`operationId`, `requestBody`, etc.).
- Never hard-code version strings like `"3.1.0"` in more than one place. Use `OPENAPI_VERSION = "3.1.0"` in `moxie/openapi/models.py`.

### Annotation Rules (v2)

- `Header[T]`, `Cookie[T]`, `Query[T]` are typed wrappers — implement them as `Annotated[T, ParamSource.HEADER]` etc. under the hood.
- Never parse annotations at request time on the hot path. All annotation inspection happens at **route registration time** and results are cached on the `Route` object.

---

## Testing (v2 — additions to v1)

### OpenAPI Tests

Every route addition must have a corresponding OpenAPI test:

```python
def test_create_item_openapi_schema():
    app = Moxie(title="Test")

    class Item(BaseModel):
        name: str

    @app.post("/items")
    async def create_item(body: Item) -> Item:
        return body

    spec = app.openapi()
    op = spec["paths"]["/items"]["post"]
    assert op["requestBody"]["content"]["application/json"]["schema"]["$ref"] == \
        "#/components/schemas/Item"
    assert spec["components"]["schemas"]["Item"]["properties"]["name"]["type"] == "string"
```

### Guard Tests

Guards must be tested in both the allow and deny paths:

```python
def test_admin_guard_blocks_unauthenticated():
    client = TestClient(app)
    response = client.delete("/users/1")
    assert response.status_code == 403
```

---

## Dependencies (v2)

### Core (always installed)

| Package | Purpose |
|---|---|
| `anyio` | Async concurrency primitives |
| `httptools` | Fast HTTP/1.1 parser |
| `h11` | HTTP/1.1 fallback |
| `pydantic>=2.0` | Schema generation + validation (now core) |

### Optional (installed via extras)

| Extra | Packages | Purpose |
|---|---|---|
| `[redis]` | `redis[asyncio]>=5.0` | Redis-backed rate limiting |
| `[yaml]` | `pyyaml` | YAML export for OpenAPI CLI |
| `[cli]` | `typer`, `rich` | `moxie` CLI tool |
| `[dev]` | `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `pyright` | Development |
| `[full]` | All of the above | |

---

## What Claude Should NOT Do (v2 — updated)

- **Do not wrap FastAPI, Starlette, or any third-party ASGI framework.** Moxie is ground-up.
- **Do not call `inspect.signature` at request time.** Signature inspection happens once at route registration; results are stored on the route object.
- **Do not generate OpenAPI outside of `moxie/openapi/`.** All spec construction lives in that package.
- **Do not serve Swagger UI or ReDoc assets from the filesystem.** Embed the HTML inline in `ui.py`.
- **Do not use `typing.Any` without `# noqa: ANN401` + justification comment.**
- **Do not add blocking I/O to any coroutine.** Use `run_in_threadpool`.
- **Do not add logging to the request hot path.** Logging is middleware only.
- **Do not generate AsyncAPI schemas** — WebSocket documentation beyond OpenAPI path entries is deferred to v3.
- **Do not call `app.openapi()` inside middleware or request handlers.** The spec is built once at startup.
- **Do not add new core dependencies without a discussion issue.**

---

## Quick Reference (v2)

```bash
# Install for development
pip install -e ".[dev,cli,yaml]"

# Format + lint + type check
ruff format moxie/ tests/ && ruff check moxie/ tests/ && pyright

# Test
pytest

# Test with coverage
pytest --cov=moxie --cov-report=term-missing

# Start dev server
moxie dev examples.crud_api:app --reload

# View all routes
moxie routes examples.crud_api:app

# Export OpenAPI spec
moxie openapi export examples.crud_api:app --output openapi.json
```

---

## Full Working Example (v2)

```python
"""examples/crud_api.py — A complete Moxie v2 CRUD API."""

from uuid import UUID, uuid4
from moxie import Moxie, HTTPException
from moxie.background import BackgroundTasks
from moxie.guards import BearerTokenGuard
from pydantic import BaseModel

app = Moxie(
    title="Items API",
    version="2.0.0",
    description="A demonstration of Moxie v2 — OpenAPI included.",
)

auth = BearerTokenGuard(scheme_name="ApiKey", validate=lambda t: t == "secret")

# ── Models ────────────────────────────────────────────────────────────────────

class ItemIn(BaseModel):
    name: str
    price: float
    in_stock: bool = True

class Item(ItemIn):
    id: UUID

# ── In-memory store ───────────────────────────────────────────────────────────

_db: dict[UUID, Item] = {}

# ── Hooks ─────────────────────────────────────────────────────────────────────

@app.on_startup
async def seed_data() -> None:
    _db[uuid4()] = Item(id=uuid4(), name="Widget", price=9.99)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/items", tags=["items"], summary="List all items")
async def list_items() -> list[Item]:
    """Return every item in the catalogue."""
    return list(_db.values())


@app.get("/items/{item_id}", tags=["items"])
async def get_item(item_id: UUID) -> Item:
    """
    Fetch a single item by ID.

    Raises:
        HTTPException(404): Item not found.
    """
    item = _db.get(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@app.post("/items", tags=["items"], guards=[auth])
async def create_item(body: ItemIn, tasks: BackgroundTasks) -> Item:
    """
    Create a new item. Requires authentication.

    Args:
        body: Item data.

    Returns:
        The created item.
    """
    item = Item(id=uuid4(), **body.model_dump())
    _db[item.id] = item
    tasks.add(print, f"[audit] created {item.id}")
    return item


@app.delete("/items/{item_id}", tags=["items"], guards=[auth])
async def delete_item(item_id: UUID) -> None:
    """
    Delete an item. Requires authentication.

    Raises:
        HTTPException(404): Item not found.
    """
    if item_id not in _db:
        raise HTTPException(404, "Item not found")
    del _db[item_id]
```

```bash
moxie dev examples.crud_api:app
# → http://localhost:8000/docs
# → http://localhost:8000/redoc
# → http://localhost:8000/openapi.json
```

---

*Last updated: see git log. This document describes Moxie v2 target architecture — implementation may be in progress.*
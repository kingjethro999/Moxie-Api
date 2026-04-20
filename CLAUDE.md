# CLAUDE.md — Moxie

> This file is the authoritative guide for Claude (and any AI assistant) working on this codebase.
> Read it fully before touching any code.

---

## Project Identity

**Name:** Moxie
**Tagline:** A fast, expressive, Python-native web framework — built for developers who want power without ceremony.
**Inspired by:** FastAPI, Starlette, Flask
**Language:** Python 3.11+
**License:** MIT

Moxie is a from-scratch ASGI web framework. It is **not** a wrapper around FastAPI or Starlette. Every component — routing, request/response lifecycle, middleware, dependency injection, validation — is written and owned by this project.

---

## Vision & Goals

Moxie exists to be:

1. **Fast by default** — async-first, zero-copy where possible, minimal allocations on the hot path.
2. **Explicit over magic** — decorators declare intent; no hidden global state, no import-time side effects.
3. **Type-safe** — leverages `typing`, `dataclasses`, and `pydantic` (optional) for request/response contracts.
4. **Composable** — routers, middleware, and apps are all first-class objects that can be mounted and combined.
5. **Batteries-optional** — a lean core with official extension packages (`moxie-auth`, `moxie-orm`, `moxie-cli`).

Non-goals:
- We do not aim to be a full-stack framework (no templating engine in core).
- We do not target WSGI. Moxie is ASGI-only.
- We do not auto-generate OpenAPI docs in v1 (planned for v2).

---

## Repository Layout

```
moxie/
├── moxie/                  # Core library source
│   ├── __init__.py         # Public re-exports
│   ├── app.py              # Moxie application class
│   ├── router.py           # Router, Route, and route registration
│   ├── request.py          # Request object
│   ├── response.py         # Response, JSONResponse, HTMLResponse, etc.
│   ├── routing/
│   │   ├── converters.py   # Path parameter type converters
│   │   └── matcher.py      # URL pattern matching engine
│   ├── middleware/
│   │   ├── base.py         # BaseMiddleware ABC
│   │   ├── cors.py         # CORS middleware
│   │   ├── gzip.py         # GZip compression middleware
│   │   └── trustedhost.py  # Trusted host enforcement
│   ├── di/
│   │   ├── container.py    # Dependency injection container
│   │   └── depends.py      # Depends() marker
│   ├── exceptions.py       # HTTPException, MoxieError hierarchy
│   ├── types.py            # Type aliases and protocols
│   └── utils/
│       ├── concurrency.py  # run_in_threadpool, asyncify helpers
│       └── encoding.py     # JSON encoding utilities
├── tests/
│   ├── conftest.py         # Shared pytest fixtures (test client, app factory)
│   ├── test_routing.py
│   ├── test_middleware.py
│   ├── test_di.py
│   ├── test_request.py
│   └── test_response.py
├── benchmarks/             # Benchmarking scripts (hypercorn, wrk)
├── docs/                   # Documentation source (MkDocs)
├── examples/               # Minimal runnable examples
├── pyproject.toml
├── CHANGELOG.md
└── CLAUDE.md               # This file
```

---

## Architecture Overview

### ASGI Lifecycle

Moxie implements the [ASGI 3.0 spec](https://asgi.readthedocs.io/en/latest/). Every `Moxie` app instance is an ASGI callable:

```python
async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

Scope types handled: `http`, `websocket`, `lifespan`.

**Request lifecycle (HTTP):**

```
ASGI server (uvicorn/hypercorn)
  └── Moxie.__call__(scope, receive, send)
        └── MiddlewareStack.dispatch(request)
              └── Router.resolve(path, method)
                    └── DependencyResolver.resolve(handler)
                          └── handler(**resolved_deps) → Response
                                └── Response.send(send)
```

### Router

- Routes are registered via decorators (`@app.get`, `@app.post`, etc.) or via a `Router` object.
- Routers can be mounted onto the main app or onto other routers.
- Path parameters use `{name}` syntax. Type converters: `{id:int}`, `{slug:str}`, `{uid:uuid}`.
- Route matching is done via a compiled trie for O(log n) dispatch.

### Request Object

`Request` wraps the raw ASGI scope/receive. It is lazy — body, JSON, and form data are not read until explicitly awaited. The `Request` object is **immutable after construction**; no handler should mutate it.

### Response Object

`Response` is the base class. Subclasses: `JSONResponse`, `HTMLResponse`, `PlainTextResponse`, `StreamingResponse`, `FileResponse`. All responses are constructed by value and call `send` once. There is no global response context.

### Dependency Injection

`Depends(callable)` marks a parameter as an injected dependency. The DI container:

1. Inspects handler signatures using `inspect.signature`.
2. Recursively resolves dependencies depth-first.
3. Caches scoped dependencies per request.
4. Supports sync and async callables.

**Scopes:** `singleton` (app lifetime), `request` (per-request), `transient` (every call).

### Middleware

Middleware wraps the entire ASGI stack. Implement `BaseMiddleware`:

```python
class MyMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        ...
        response = await call_next(request)
        ...
        return response
```

Middleware is applied in registration order (outermost first).

---

## Coding Standards

### Python Style

- **Formatter:** `ruff format` (line length 88)
- **Linter:** `ruff check` (rules: `E`, `F`, `I`, `UP`, `B`, `SIM`)
- **Type checking:** `pyright` in strict mode
- All public functions and methods **must** have type annotations.
- All public APIs **must** have docstrings (Google style).
- Private helpers use a leading underscore: `_resolve_deps`.

### Async Rules

- Prefer `async def` for all I/O-touching code.
- Never call blocking I/O (file reads, `requests`, `time.sleep`) from a coroutine directly. Use `run_in_threadpool`.
- Never use `asyncio.get_event_loop()`. Use `asyncio.get_running_loop()` or `anyio`.
- Task creation must be scoped; do not fire-and-forget without a handle.

### Error Handling

- User-facing HTTP errors always raise `HTTPException(status_code=..., detail=...)`.
- Internal errors raise domain-specific `MoxieError` subclasses (never bare `Exception`).
- Handlers must not swallow exceptions silently. Log and re-raise or convert.
- Exception handlers registered via `@app.exception_handler(ExcType)` must return a `Response`.

### Imports

- Absolute imports only. No relative imports in library code.
- Import order enforced by `ruff` (stdlib → third-party → local).
- `TYPE_CHECKING` guard for imports used only in annotations.

### No Global State

- No module-level mutable singletons (no `_app = None` patterns).
- No `threading.local` or `contextvars` unless explicitly scoped to a request context.
- The `Moxie` app instance is the unit of state.

---

## Testing

**Framework:** `pytest` + `pytest-asyncio`
**Test client:** `moxie.testclient.TestClient` (wraps the ASGI app with `httpx`)

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=moxie --cov-report=term-missing

# A specific file
pytest tests/test_routing.py -v

# Only fast tests (exclude benchmark/integration markers)
pytest -m "not slow"
```

### Test Rules

- Every public function must have at least one test.
- Tests are **pure** — no real network calls, no filesystem writes outside `tmp_path`.
- Each test function tests one behaviour. No multi-assertion omnibus tests.
- Fixtures live in `conftest.py`; no fixture logic inside test functions.
- Test names follow: `test_<what>_<condition>_<expected>`.

### Test Client

```python
from moxie.testclient import TestClient

def test_hello_returns_200():
    app = Moxie()

    @app.get("/hello")
    async def hello() -> dict:
        return {"message": "hi"}

    client = TestClient(app)
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hi"}
```

---

## Common Tasks

### Adding a New Response Type

1. Add class to `moxie/response.py` extending `Response`.
2. Set `media_type` class attribute.
3. Override `render(content)` if custom serialization is needed.
4. Re-export from `moxie/__init__.py`.
5. Add tests in `tests/test_response.py`.

### Adding a New Path Converter

1. Add converter class to `moxie/routing/converters.py` implementing `Converter` protocol.
2. Register it in `CONVERTERS` dict at the bottom of that file.
3. Add tests in `tests/test_routing.py` covering valid and invalid inputs.

### Adding Middleware

1. Implement in `moxie/middleware/<name>.py` extending `BaseMiddleware`.
2. Export from `moxie/middleware/__init__.py`.
3. Document all configuration parameters.
4. Add tests covering both the pass-through case and the middleware's effect.

### Adding a Dependency Scope

1. Add the scope string constant to `moxie/di/container.py`.
2. Implement the caching strategy inside `DependencyContainer.resolve()`.
3. Document the scope's lifetime clearly in the docstring.

---

## Performance Rules

These rules apply to the **hot path** (request parsing, routing, response sending). They do not apply to startup code.

- No string formatting (`f-string`, `.format()`) on the hot path. Pre-compute or use byte literals.
- No `isinstance` chains longer than 3. Use a dispatch dict or protocol.
- No `dict.copy()` or list construction where mutation of the original is safe.
- Avoid attribute lookup inside tight loops — hoist to a local variable.
- Use `__slots__` on `Request`, `Response`, and `Route` objects.
- Profile before optimizing. Keep `benchmarks/` updated.

---

## Dependencies

### Core (always installed)
| Package | Purpose |
|---|---|
| `anyio` | Async concurrency primitives |
| `httptools` | Fast HTTP/1.1 parser |
| `h11` | HTTP/1.1 state machine (fallback) |

### Optional (installed via extras)
| Extra | Packages | Purpose |
|---|---|---|
| `[validation]` | `pydantic>=2.0` | Request/response validation |
| `[dev]` | `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `pyright` | Development tools |
| `[full]` | All of the above | |

**Do not add new core dependencies without opening a discussion issue first.** Every new dependency must be evaluated for: binary size, transitive deps, maintenance status, and license compatibility.

---

## Versioning & Changelog

- Moxie follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`).
- `MAJOR` bump: any breaking change to the public API.
- `MINOR` bump: new backwards-compatible feature.
- `PATCH` bump: bug fix or internal refactor with no API change.
- Every PR that touches public API **must** include an entry in `CHANGELOG.md` under `## [Unreleased]`.
- Format: `### Added | Changed | Deprecated | Removed | Fixed | Security`.

---

## What Claude Should NOT Do

- **Do not import FastAPI, Starlette, or Django** in library code. Moxie is ground-up.
- **Do not use `typing.Any` as a shortcut.** Every `Any` usage must have a `# noqa: ANN401` comment with a justification.
- **Do not modify `pyproject.toml` dependencies** without explicit instruction.
- **Do not add logging calls in request hot path.** Logging belongs in middleware or lifecycle hooks.
- **Do not write tests that call real external services.** Mock or use fakes.
- **Do not generate OpenAPI schemas** — that feature is explicitly deferred to v2.
- **Do not introduce sync-only APIs.** All public I/O APIs must be async.

---

## Quick Reference

```bash
# Install for development
pip install -e ".[dev]"

# Format
ruff format moxie/ tests/

# Lint
ruff check moxie/ tests/

# Type check
pyright

# Test
pytest

# Run an example
uvicorn examples.hello:app --reload
```

---

## Minimal Working Example

```python
from moxie import Moxie, JSONResponse

app = Moxie()

@app.get("/")
async def index() -> dict:
    return {"framework": "Moxie", "status": "running"}

@app.get("/greet/{name:str}")
async def greet(name: str) -> JSONResponse:
    return JSONResponse({"hello": name})
```

```bash
uvicorn myapp:app
```

---

*Last updated: see git log.*

for upgrade see @CLAUDE.V2.md
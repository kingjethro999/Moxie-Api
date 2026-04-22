import pytest

from moxie import Moxie
from moxie.middleware import (
    CORSMiddleware,
    HTTPSRedirectMiddleware,
    TrustedHostMiddleware,
)


@pytest.mark.asyncio
async def test_cors_middleware():
    app = Moxie()
    app.add_middleware(CORSMiddleware, allow_origins=["*"])

    @app.get("/")
    async def index():
        return {"hello": "world"}

    # Mock ASGI scope for a CORS request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"origin", b"http://example.com")],
    }
    
    headers_received = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        if message["type"] == "http.response.start":
            headers_received.extend(message["headers"])

    await app(scope, receive, send)

    # Check if CORS header is present
    header_names = [h[0] for h in headers_received]
    assert b"access-control-allow-origin" in header_names

@pytest.mark.asyncio
async def test_trusted_host_middleware():
    app = Moxie()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])

    @app.get("/")
    async def index():
        return {"hello": "world"}

    # Mock ASGI scope for an allowed host
    scope_allowed = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"host", b"example.com")],
    }
    
    status_code = [0]

    async def send(message):
        if message["type"] == "http.response.start":
            status_code[0] = message["status"]

    await app(scope_allowed, lambda: {"type": "http.request"}, send)
    assert status_code[0] == 200

    # Mock ASGI scope for a disallowed host
    scope_disallowed = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"host", b"malicious.com")],
    }
    
    await app(scope_disallowed, lambda: {"type": "http.request"}, send)
    assert status_code[0] == 400

@pytest.mark.asyncio
async def test_https_redirect_middleware():
    app = Moxie()
    app.add_middleware(HTTPSRedirectMiddleware)

    @app.get("/")
    async def index():
        return {"hello": "world"}

    scope = {
        "type": "http",
        "scheme": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"host", b"example.com")],
    }
    
    response_data = {}

    async def send(message):
        if message["type"] == "http.response.start":
            response_data["status"] = message["status"]
            response_data["headers"] = dict(message["headers"])

    await app(scope, lambda: {"type": "http.request"}, send)
    
    assert response_data["status"] == 307
    assert response_data["headers"][b"location"] == b"https://example.com/"

from collections.abc import Mapping
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None # type: ignore


class TestClient:
    """
    A simple test client for Moxie apps using httpx.ASGITransport.
    """
    def __init__(
        self, 
        app: Any, 
        base_url: str = "http://testserver",
        headers: Mapping[str, str] | None = None
    ) -> None:
        if httpx is None:
            raise ImportError(
                "TestClient requires 'httpx' to be installed. "
                "Install it with 'pip install httpx'."
            )
        self.app = app
        self.client = httpx.Client(
            transport=httpx.ASGITransport(app=app), 
            base_url=base_url,
            headers=headers
        )

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.post(url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.put(url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.delete(url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.patch(url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return self.client.request(method, url, **kwargs)

    def websocket_connect(self, url: str, **kwargs: Any) -> Any:
        # Note: WebSockets require httpx to be used in an async context or a
        # different tool. For simplicity, we'll just note it's not fully
        # supported in this sync wrapper.
        raise NotImplementedError("WebSocket testing requires an async TestClient.")

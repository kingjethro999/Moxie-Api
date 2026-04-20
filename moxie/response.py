import json
from typing import Any, AsyncIterable, Dict, Iterable, Optional, Union
from moxie.types import Send

class Response:
    __slots__ = ("content", "status_code", "headers", "media_type")
    
    # We define media_type as a class variable in subclasses, 
    # but in the base class we'll just handle it in __init__.
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        
        # Use provided media_type or the class-level one
        self.media_type = media_type or getattr(self, "media_type", None)
        
        if self.media_type and "content-type" not in self.headers:
            self.headers["content-type"] = self.media_type

    async def __call__(self, send: Send) -> None:
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": [
                [k.lower().encode("latin-1"), v.encode("latin-1")]
                for k, v in self.headers.items()
            ],
        })
        body = self.render(self.content)
        await send({
            "type": "http.response.body",
            "body": body,
        })

    def render(self, content: Any) -> bytes:
        if content is None:
            return b""
        if isinstance(content, bytes):
            return content
        return str(content).encode("utf-8")

class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

class HTMLResponse(Response):
    media_type = "text/html; charset=utf-8"

class PlainTextResponse(Response):
    media_type = "text/plain; charset=utf-8"

class StreamingResponse(Response):
    __slots__ = ("streaming_content",)
    
    def __init__(
        self,
        content: AsyncIterable[Any],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None:
        super().__init__(None, status_code, headers, media_type)
        self.streaming_content = content

    async def __call__(self, send: Send) -> None:
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": [
                [k.lower().encode("latin-1"), v.encode("latin-1")]
                for k, v in self.headers.items()
            ],
        })
        async for chunk in self.streaming_content:
            if not isinstance(chunk, bytes):
                chunk = str(chunk).encode("utf-8")
            await send({
                "type": "http.response.body",
                "body": chunk,
                "more_body": True,
            })
        await send({
            "type": "http.response.body",
            "body": b"",
            "more_body": False,
        })

class EventSourceResponse(StreamingResponse):
    media_type = "text/event-stream"
    __slots__ = ("ping_interval",)

    def __init__(
        self,
        content: AsyncIterable[Any],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        ping_interval: int = 15,
    ) -> None:
        headers = headers or {}
        headers.setdefault("Cache-Control", "no-cache")
        headers.setdefault("Connection", "keep-alive")
        super().__init__(content, status_code, headers, self.media_type)
        self.ping_interval = ping_interval

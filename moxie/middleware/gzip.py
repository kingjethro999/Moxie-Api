import gzip
import io
from typing import Any

from moxie.middleware.base import ASGIMiddleware


class GZipMiddleware(ASGIMiddleware):
    def __init__(
        self,
        app: Any,
        minimum_size: int = 500,
        compresslevel: int = 9,
    ) -> None:
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        if b"gzip" not in headers.get(b"accept-encoding", b""):
            await self.app(scope, receive, send)
            return

        responder = GZipResponder(self.app, self.minimum_size, self.compresslevel)
        await responder(scope, receive, send)


class GZipResponder:
    def __init__(self, app: Any, minimum_size: int, compresslevel: int) -> None:
        self.app = app
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel
        self.send: Any = None
        self.initial_message: dict[str, Any] = {}
        self.started = False
        self.gzip_buffer = io.BytesIO()
        self.gzip_file = gzip.GzipFile(
            mode="wb", fileobj=self.gzip_buffer, compresslevel=self.compresslevel
        )

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.send = send
        await self.app(scope, receive, self.send_wrapper)

    async def send_wrapper(self, message: dict[str, Any]) -> None:
        message_type = message["type"]

        if message_type == "http.response.start":
            self.initial_message = message
        elif message_type == "http.response.body" and not self.started:
            self.started = True
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            if len(body) < self.minimum_size and not more_body:
                # Too small to compress
                await self.send(self.initial_message)
                await self.send(message)
            elif not more_body:
                # Standard response, compress in one go
                self.gzip_file.write(body)
                self.gzip_file.close()
                compressed_body = self.gzip_buffer.getvalue()

                headers = list(self.initial_message.get("headers", []))
                headers.append((b"content-encoding", b"gzip"))
                headers.append((b"vary", b"Accept-Encoding"))
                
                # Update Content-Length if present
                new_headers = []
                for k, v in headers:
                    if k.lower() != b"content-length":
                        new_headers.append((k, v))
                compressed_size = str(len(compressed_body)).encode()
                new_headers.append((b"content-length", compressed_size))
                
                self.initial_message["headers"] = new_headers
                await self.send(self.initial_message)
                
                message["body"] = compressed_body
                await self.send(message)
            else:
                # Streaming response, start compression
                headers = list(self.initial_message.get("headers", []))
                headers.append((b"content-encoding", b"gzip"))
                headers.append((b"vary", b"Accept-Encoding"))
                
                # Content-Length is invalid for streaming compressed content
                new_headers = [
                    (k, v) for k, v in headers if k.lower() != b"content-length"
                ]
                self.initial_message["headers"] = new_headers
                
                await self.send(self.initial_message)
                self.gzip_file.write(body)
                message["body"] = self.gzip_buffer.getvalue()
                self.gzip_buffer.seek(0)
                self.gzip_buffer.truncate()
                await self.send(message)
        elif message_type == "http.response.body" and self.started:
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            self.gzip_file.write(body)
            if not more_body:
                self.gzip_file.close()
            
            message["body"] = self.gzip_buffer.getvalue()
            self.gzip_buffer.seek(0)
            self.gzip_buffer.truncate()
            await self.send(message)
        else:
            await self.send(message)

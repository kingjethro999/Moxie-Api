import json
import time
import logging
from typing import Any
from moxie.middleware.base import ASGIMiddleware

logger = logging.getLogger("moxie.request")

class StructuredLoggingMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request_id = scope.get("request_id", "unknown")
        
        status_code = [0] # Use a list to allow mutation in the wrapper

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = (time.perf_counter() - start_time) * 1000
            log_data = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "status": status_code[0],
                "duration_ms": round(duration, 2),
                "client_ip": scope.get("client", ["unknown"])[0]
            }
            logger.info(json.dumps(log_data))

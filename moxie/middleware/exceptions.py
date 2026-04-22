import logging
from typing import Any

from moxie.exceptions import HTTPException
from moxie.middleware.base import ASGIMiddleware
from moxie.response import JSONResponse

logger = logging.getLogger("moxie")

class ServerErrorMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger.exception("Unhandled exception")
            
            from pydantic import ValidationError
            
            if isinstance(exc, HTTPException):
                response = JSONResponse(
                    {"detail": exc.detail}, 
                    status_code=exc.status_code,
                    headers=exc.headers
                )
            elif isinstance(exc, ValidationError):
                response = JSONResponse(
                    {"detail": exc.errors()},
                    status_code=422
                )
            else:
                # In production, you might want to hide details
                response = JSONResponse(
                    {"detail": "Internal Server Error"}, 
                    status_code=500
                )
            
            await response(send)

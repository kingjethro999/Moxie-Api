from typing import Any, Dict, Optional
from moxie.guards.base import BaseGuard
from moxie.request import Request
from moxie.exceptions import HTTPException

class BearerTokenGuard(BaseGuard):
    def __init__(self, scheme_name: str = "BearerAuth", description: Optional[str] = None) -> None:
        self.scheme_name = scheme_name
        self.openapi_security_scheme = {
            "type": "http",
            "scheme": "bearer",
        }
        if description:
            self.openapi_security_scheme["description"] = description

    async def check(self, request: Request) -> None:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, detail="Invalid or missing bearer token")
        
        # Note: subclasses should override this and validate the token
        # then perhaps store the user in request.scope["user"]

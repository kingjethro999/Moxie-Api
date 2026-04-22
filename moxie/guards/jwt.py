from typing import Any

from moxie.guards.bearer import BearerTokenGuard
from moxie.request import Request


class JWTGuard(BearerTokenGuard):
    def __init__(
        self, 
        scheme_name: str = "JWTAuth", 
        description: str = "JSON Web Token (JWT) Authentication",
        **kwargs: Any
    ) -> None:
        super().__init__(scheme_name=scheme_name, description=description)
        self.kwargs = kwargs

    async def check(self, request: Request) -> None:
        # First check the bearer format
        await super().check(request)
        
        auth_header = request.headers.get("authorization")
        token = auth_header.split(" ")[1] # type: ignore (Checked in super().check)
        
        # Subclasses should implement decoding and validation
        # Example using PyJWT:
        # try:
        #     payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        #     request.scope["user"] = payload
        # except jwt.ExpiredSignatureError:
        #     raise HTTPException(401, detail="Token has expired")
        # except jwt.InvalidTokenError:
        #     raise HTTPException(401, detail="Invalid token")
        
        request.scope["auth_token"] = token

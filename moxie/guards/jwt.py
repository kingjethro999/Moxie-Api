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
        
        await self.validate(token, request)
        request.scope["auth_token"] = token

    async def validate(self, token: str, request: Request) -> None:
        """
        Validate the JWT token. 
        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses of JWTGuard must implement the 'validate' method."
        )

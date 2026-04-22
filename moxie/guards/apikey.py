from moxie.exceptions import HTTPException
from moxie.guards.base import BaseGuard
from moxie.request import Request


class APIKeyGuard(BaseGuard):
    def __init__(
        self, 
        name: str = "X-API-Key", 
        in_query: bool = False,
        scheme_name: str = "ApiKeyAuth", 
        description: str | None = None
    ) -> None:
        self.name = name
        self.in_query = in_query
        self.scheme_name = scheme_name
        self.openapi_security_scheme = {
            "type": "apiKey",
            "name": name,
            "in": "query" if in_query else "header",
        }
        if description:
            self.openapi_security_scheme["description"] = description

    async def check(self, request: Request) -> None:
        if self.in_query:
            api_key = request.query_params.get(self.name)
        else:
            api_key = request.headers.get(self.name.lower())

        if not api_key:
            raise HTTPException(401, detail=f"Missing API Key: {self.name}")
        
        # Subclasses should validate the api_key here

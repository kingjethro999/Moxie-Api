
class MoxieError(Exception):
    """Base class for all Moxie exceptions."""

class HTTPException(MoxieError):
    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail or "An error occurred."
        self.headers = headers

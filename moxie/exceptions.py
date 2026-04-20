from typing import Any, Dict, Optional

class MoxieError(Exception):
    """Base class for all Moxie exceptions."""

class HTTPException(MoxieError):
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail or "An error occurred."
        self.headers = headers

import mimetypes
import os
from typing import Any

from moxie.response import FileResponse, PlainTextResponse


class StaticFiles:
    def __init__(
        self, 
        directory: str, 
        html: bool = False, 
        check_dir: bool = True
    ) -> None:
        self.directory = directory
        self.html = html
        if check_dir and not os.path.isdir(directory):
            raise RuntimeError(f"Directory '{directory}' does not exist")

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        assert scope["type"] == "http"
        
        if scope["method"] not in ("GET", "HEAD"):
            response = PlainTextResponse("Method Not Allowed", status_code=405)
            await response(send)
            return

        path = self._get_path(scope)
        full_path = os.path.join(self.directory, path)

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            if self.html:
                # Try index.html
                index_path = os.path.join(full_path, "index.html")
                if os.path.exists(index_path):
                    full_path = index_path
                else:
                    response = PlainTextResponse("Not Found", status_code=404)
                    await response(send)
                    return
            else:
                response = PlainTextResponse("Not Found", status_code=404)
                await response(send)
                return

        # Basic security: prevent directory traversal
        abs_directory = os.path.abspath(self.directory)
        abs_full_path = os.path.abspath(full_path)
        if not abs_full_path.startswith(abs_directory):
             response = PlainTextResponse("Forbidden", status_code=403)
             await response(send)
             return

        stat = os.stat(full_path)
        content_type, _ = mimetypes.guess_type(full_path)
        content_type = content_type or "application/octet-stream"

        response = FileResponse(
            full_path, 
            status_code=200, 
            headers={
                "content-type": content_type,
                "content-length": str(stat.st_size),
                "last-modified": self._format_date(stat.st_mtime),
            }
        )
        await response(send)

    def _get_path(self, scope: Any) -> str:
        path = scope["path"]
        if path.startswith("/"):
            path = path[1:]
        return path

    def _format_date(self, timestamp: float) -> str:
        import time
        return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp))

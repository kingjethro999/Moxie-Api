from typing import Any, Callable, List, Optional, Union
from moxie.app import Moxie
from moxie.plugins import BasePlugin
from moxie.response import JSONResponse

class HealthCheck:
    def __init__(self, name: str, check_func: Callable[[], Any]) -> None:
        self.name = name
        self.check_func = check_func

    async def execute(self) -> bool:
        try:
            import inspect
            if inspect.iscoroutinefunction(self.check_func):
                await self.check_func()
            else:
                self.check_func()
            return True
        except Exception:
            return False

class HealthPlugin(BasePlugin):
    name = "health"

    def __init__(self, checks: Optional[List[HealthCheck]] = None) -> None:
        self.checks = checks or []

    async def on_startup(self, app: Moxie) -> None:
        @app.get("/healthz", include_in_schema=False, tags=["Health"])
        async def liveness() -> dict:
            return {"status": "ok"}

        @app.get("/readyz", include_in_schema=False, tags=["Health"])
        async def readiness() -> JSONResponse:
            results = {}
            all_ok = True
            for check in self.checks:
                ok = await check.execute()
                results[check.name] = "ok" if ok else "failed"
                if not ok:
                    all_ok = False
            
            status_code = 200 if all_ok else 503
            return JSONResponse(
                {"status": "ok" if all_ok else "unready", "checks": results},
                status_code=status_code
            )

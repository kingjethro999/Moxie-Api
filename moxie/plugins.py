from typing import Any, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from moxie.app import Moxie

class Plugin(Protocol):
    name: str

    async def on_startup(self, app: "Moxie") -> None: ...
    async def on_shutdown(self, app: "Moxie") -> None: ...

class BasePlugin:
    name: str = "base"

    async def on_startup(self, app: "Moxie") -> None:
        pass

    async def on_shutdown(self, app: "Moxie") -> None:
        pass

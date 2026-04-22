from typing import TYPE_CHECKING, Any

from moxie.plugins import BasePlugin

if TYPE_CHECKING:
    from moxie.app import Moxie

class SupabasePlugin(BasePlugin):
    """
    A plugin to easily integrate Supabase into Moxie.
    
    Reads from SUPABASE_URL and SUPABASE_KEY if not provided.
    """
    name: str = "supabase"

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        from moxie.config import Settings
        settings = Settings("SUPABASE")
        
        self.url = url or settings.get("URL")
        self.key = key or settings.get("KEY")
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and Key must be provided either in __init__ "
                "or via SUPABASE_URL and SUPABASE_KEY environment variables."
            )
        
        self.client: Any = None

    async def on_startup(self, app: "Moxie") -> None:
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            # Register the client in the DI container so it can be injected
            app.di_container.singleton_cache[self.get_client] = self.client
        except ImportError:
            raise ImportError(
                "Supabase client not found. Install it with 'pip install supabase'."
            ) from None

    def get_client(self) -> Any:
        return self.client

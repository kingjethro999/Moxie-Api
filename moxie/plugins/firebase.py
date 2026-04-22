from typing import TYPE_CHECKING, Any

from moxie.plugins import BasePlugin

if TYPE_CHECKING:
    from moxie.app import Moxie

class FirebasePlugin(BasePlugin):
    """
    A plugin to easily integrate Firebase into Moxie.
    
    Reads from FIREBASE_CREDENTIALS if credential_path is not provided.
    """
    name: str = "firebase"

    def __init__(
        self, 
        credential_path: str | None = None, 
        options: dict[str, Any] | None = None
    ) -> None:
        from moxie.config import Settings
        settings = Settings("FIREBASE")
        
        self.credential_path = credential_path or settings.get("CREDENTIALS")
        self.options = options or {}
        self.admin: Any = None

    async def on_startup(self, app: "Moxie") -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            if not firebase_admin._apps:
                if self.credential_path:
                    cred = credentials.Certificate(self.credential_path)
                    self.admin = firebase_admin.initialize_app(cred, self.options)
                else:
                    self.admin = firebase_admin.initialize_app(options=self.options)
            
            # Register in DI
            app.di_container.singleton_cache[firebase_admin.App] = self.admin
        except ImportError:
            raise ImportError(
                "Firebase Admin SDK is not installed. "
                "Install it with 'pip install firebase-admin'."
            ) from None

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from moxie.plugins import BasePlugin

if TYPE_CHECKING:
    from moxie.app import Moxie

class SQLAlchemyPlugin(BasePlugin):
    """
    A plugin to integrate SQLAlchemy (Async) into Moxie.
    
    Reads from DATABASE_URL if database_url is not provided.
    """
    name: str = "sqlalchemy"

    def __init__(self, database_url: str | None = None, **engine_kwargs: Any) -> None:
        from moxie.config import Settings
        settings = Settings() # Root settings or we could use prefix "DB"
        
        self.database_url = database_url or settings.get("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError(
                "Database URL must be provided either in __init__ "
                "or via DATABASE_URL environment variable."
            )
            
        self.engine_kwargs = engine_kwargs
        self.engine: Any = None
        self.session_maker: Any = None

    async def on_startup(self, app: "Moxie") -> None:
        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
            
            self.engine = create_async_engine(self.database_url, **self.engine_kwargs)
            self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
            
            # Register the session getter in DI as a dependency
            # This allows injection via Depends(db_plugin.get_db)
            app.di_container.singleton_cache[type(self.engine)] = self.engine
        except ImportError:
            raise ImportError(
                "SQLAlchemy is not installed. Install it with 'pip install sqlalchemy'."
            ) from None

    async def on_shutdown(self, app: "Moxie") -> None:
        if self.engine:
            await self.engine.dispose()

    async def get_db(self) -> AsyncGenerator[Any, None]:
        """Dependency to get a database session."""
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

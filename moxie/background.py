import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("moxie.background")

class BackgroundTasks:
    def __init__(self) -> None:
        self.tasks: list[
            tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]
        ] = []

    def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.tasks.append((func, args, kwargs))

    def add_concurrent(
        self, tasks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]]
    ) -> None:
        self.tasks.extend(tasks)

    async def run(self) -> None:
        if not self.tasks:
            return

        import anyio

        async with anyio.create_task_group() as tg:
            for func, args, kwargs in self.tasks:
                if inspect.iscoroutinefunction(func):
                    if kwargs:
                        # anyio start_soon doesn't support kwargs, so we wrap
                        async def wrapper(f=func, a=args, k=kwargs):
                            await f(*a, **k)
                        tg.start_soon(wrapper)
                    else:
                        tg.start_soon(func, *args)
                else:
                    # Run sync functions in thread pool
                    def sync_wrapper(f=func, a=args, k=kwargs):
                        try:
                            f(*a, **k)
                        except Exception as exc:
                            logger.error(
                                f"Error in sync background task {f.__name__}: {exc}"
                            )
                    
                    tg.start_soon(anyio.to_thread.run_sync, sync_wrapper)

import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("moxie.background")

class BackgroundTasks:
    def __init__(self) -> None:
        self.tasks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = []

    def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.tasks.append((func, args, kwargs))

    def add_concurrent(self, tasks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]]) -> None:
        # Placeholder for parallel execution if needed
        self.tasks.extend(tasks)

    async def run(self) -> None:
        for func, args, kwargs in self.tasks:
            try:
                if inspect.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            except Exception as exc:
                logger.error(f"Error in background task {func.__name__}: {exc}")

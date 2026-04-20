import functools
from typing import Any, Callable, TypeVar
import anyio

T = TypeVar("T")

async def run_in_threadpool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a sync function in an anyio worker thread."""
    if kwargs:
        func = functools.partial(func, **kwargs)
    return await anyio.to_thread.run_sync(func, *args)

def asyncify(func: Callable[..., T]) -> Callable[..., Any]:
    """Decorator to run a sync function in a threadpool when called as async."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await run_in_threadpool(func, *args, **kwargs)
    return wrapper

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any
from functools import wraps

_executor: ThreadPoolExecutor | None = None

def get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor

async def run_in_threadpool(func: Callable, *args, **kwargs) -> Any:
    loop = asyncio.get_event_loop()
    executor = get_executor()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

def async_cpu_bound(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_threadpool(func, *args, **kwargs)
    return wrapper

"""
TODO:

`run_async` takes an awaitable integer.
"""


import asyncio
from typing import Awaitable

def run_async(awaitable: Awaitable[int]) -> int:
    async def run_wrapper() -> int:
        return await awaitable

    return asyncio.run(run_wrapper())
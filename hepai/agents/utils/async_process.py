import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Generator

def sync_wrapper(async_gen: AsyncGenerator) -> Generator:
    loop = asyncio.new_event_loop()
    with ThreadPoolExecutor(1) as executor:
        while True:
            try:
                yield executor.submit(
                    lambda: loop.run_until_complete(async_gen.__anext__())
                ).result()
            except StopAsyncIteration:
                break
    loop.close()
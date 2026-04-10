from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx

@asynccontextmanager
async def get_http_client(
    base_url: str,
    timeout: float = 30.0
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client

        
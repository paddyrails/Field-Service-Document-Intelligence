import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


async def resilient_request(
    method: str,
    url: str,
    service_name: str,
    **kwargs,
) -> httpx.Response:

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    )
    async def _call():
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, timeout=10.0, **kwargs)
            response.raise_for_status()
            return response

    return await _call()

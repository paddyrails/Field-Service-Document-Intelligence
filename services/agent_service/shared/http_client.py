import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_breakers: dict[str, pybreaker.CircuitBreaker] = {}

def _get_breaker(name: str) -> pybreaker.CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = pybreaker.CircuitBreaker(
            fail_max=5, reset_timeout=30, name=name
        )
    return _breakers


async def resilient_request(
        method: str,
        url: str,
        service_name: str,
        **kwargs
)-> httpx.Response:
    breaker = _get_breaker(service_name)

    @breaker
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
        
    return await _call
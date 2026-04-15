from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.router import contract_router, visit_router
from common.database.client import close_client
from common.exceptions.handlers import (
    ContractNotFoundError,
    VisitNotFoundError,
    contract_not_found_handler,
    visit_not_found_handler,
)
from common.limiter.rate_limiter import limiter
from common.logging.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield
    await close_client()


app = FastAPI(
    title="RiteCare BU2 - Sales & Maintenance",
    description="API for managing service contracts and field visits",
    version="0.1.0",
    root_path="/bu2",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(ContractNotFoundError, contract_not_found_handler)
app.add_exception_handler(VisitNotFoundError, visit_not_found_handler)

app.include_router(contract_router)
app.include_router(visit_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "bu2-sales-maintenance"}

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.router import ingest_router, router
from common.config import settings
from common.database.client import close_client
from common.exceptions.handlers import (
    CustomerNotFoundError,
    DuplicateCustomerError,
    customer_not_found_handler,
    duplicate_customer_handler,
)
from common.limiter.limiter import limiter
from common.logging.logger import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield
    await close_client()

app = FastAPI(
    title="RiteCare BU1 - Customer Onboarding",
    description="API for managing customer onboarding processes",
    version="0.1.0",
    root_path="/bu1",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(CustomerNotFoundError, customer_not_found_handler)
app.add_exception_handler(DuplicateCustomerError, duplicate_customer_handler)   
app.include_router(router)
app.include_router(ingest_router)

@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "bu1-onboarding"}
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.router import router
from common.database.client import close_client
from common.exceptions.handlers import (
    TicketAlreadyClosedError,
    TicketNotFoundError,
    ticket_already_closed_handler,
    ticket_not_found_handler,
)
from common.limiter.rate_limiter import limiter
from common.logging.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield
    await close_client()


app = FastAPI(
    title="RiteCare BU4 - Support & Fulfillment",
    description="API for managing customer support tickets",
    version="0.1.0",
    root_path="/bu4",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(TicketNotFoundError, ticket_not_found_handler)
app.add_exception_handler(TicketAlreadyClosedError, ticket_already_closed_handler)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "bu4-support-fulfillment"}

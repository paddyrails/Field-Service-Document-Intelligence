from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.router import invoice_router, subscription_router
from common.database.client import close_client
from common.exceptions.handlers import (
    InvoiceAlreadyPaidError,
    InvoiceNotFoundError,
    SubscriptionNotFoundError,
    invoice_already_paid_handler,
    invoice_not_found_handler,
    subscription_not_found_handler,
)
from common.limiter.rate_limiter import limiter
from common.logging.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield
    await close_client()


app = FastAPI(
    title="RiteCare BU3 - Billing & Subscription",
    description="API for managing customer billing, invoices, and subscriptions",
    version="0.1.0",
    root_path="/bu3",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(InvoiceNotFoundError, invoice_not_found_handler)
app.add_exception_handler(SubscriptionNotFoundError, subscription_not_found_handler)
app.add_exception_handler(InvoiceAlreadyPaidError, invoice_already_paid_handler)

app.include_router(invoice_router)
app.include_router(subscription_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "bu3-billing-subscription"}

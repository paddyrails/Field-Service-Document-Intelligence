from fastapi import Request
from fastapi.responses import JSONResponse


class InvoiceNotFoundError(Exception):
    def __init__(self, invoice_id: str) -> None:
        self.invoice_id = invoice_id


class SubscriptionNotFoundError(Exception):
    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id


class InvoiceAlreadyPaidError(Exception):
    def __init__(self, invoice_id: str) -> None:
        self.invoice_id = invoice_id


async def invoice_not_found_handler(
    request: Request, exc: InvoiceNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Invoice '{exc.invoice_id}' not found"},
    )


async def subscription_not_found_handler(
    request: Request, exc: SubscriptionNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Subscription for customer '{exc.customer_id}' not found"},
    )


async def invoice_already_paid_handler(
    request: Request, exc: InvoiceAlreadyPaidError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": f"Invoice '{exc.invoice_id}' is already paid"},
    )

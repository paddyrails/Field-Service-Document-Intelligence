from fastapi import APIRouter, Depends

from api.dependencies import get_invoice_service, get_subscription_service
from common.schemas.request import (
    InvoiceCreateRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
)
from common.schemas.response import InvoiceResponse, SubscriptionResponse
from service.invoice_service import InvoiceService
from service.subscription_service import SubscriptionService

invoice_router = APIRouter(prefix="/invoices", tags=["invoices"])
subscription_router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@invoice_router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    body: InvoiceCreateRequest,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    return await service.create_invoice(body)


@invoice_router.get("/{customer_id}", response_model=list[InvoiceResponse])
async def list_invoices(
    customer_id: str,
    service: InvoiceService = Depends(get_invoice_service),
) -> list[InvoiceResponse]:
    return await service.list_invoices(customer_id)


@invoice_router.patch("/{invoice_id}/pay", response_model=InvoiceResponse)
async def pay_invoice(
    invoice_id: str,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    return await service.pay_invoice(invoice_id)


@subscription_router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    body: SubscriptionCreateRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.create_subscription(body)


@subscription_router.get("/{customer_id}", response_model=SubscriptionResponse)
async def get_subscription(
    customer_id: str,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.get_subscription(customer_id)


@subscription_router.patch("/{customer_id}", response_model=SubscriptionResponse)
async def update_subscription(
    customer_id: str,
    body: SubscriptionUpdateRequest,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.update_subscription(customer_id, body)

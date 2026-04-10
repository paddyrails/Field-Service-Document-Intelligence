from common.exceptions.handlers import InvoiceAlreadyPaidError, InvoiceNotFoundError
from common.models.invoice import Invoice, InvoiceStatus
from common.schemas.request import InvoiceCreateRequest
from common.schemas.response import InvoiceResponse
from dao.invoice_dao import InvoiceDAO


class InvoiceService:
    def __init__(self, dao: InvoiceDAO) -> None:
        self.dao = dao

    async def create_invoice(self, request: InvoiceCreateRequest) -> InvoiceResponse:
        invoice = Invoice(
            customer_id=request.customer_id,
            amount=request.amount,
            due_date=request.due_date,
            description=request.description,
        )
        invoice_id = await self.dao.insert(invoice)
        created = await self.dao.find_by_id(invoice_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def list_invoices(self, customer_id: str) -> list[InvoiceResponse]:
        invoices = await self.dao.find_by_customer(customer_id)
        return [self._to_response(i) for i in invoices]

    async def pay_invoice(self, invoice_id: str) -> InvoiceResponse:
        invoice = await self.dao.find_by_id(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise InvoiceAlreadyPaidError(invoice_id)
        await self.dao.mark_paid(invoice_id)
        updated = await self.dao.find_by_id(invoice_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    def _to_response(self, invoice: Invoice) -> InvoiceResponse:
        return InvoiceResponse(
            id=str(invoice.id),
            customer_id=invoice.customer_id,
            amount=invoice.amount,
            due_date=invoice.due_date,
            status=invoice.status,
            description=invoice.description,
            paid_at=invoice.paid_at,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

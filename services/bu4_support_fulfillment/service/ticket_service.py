from common.exceptions.handlers import TicketAlreadyClosedError, TicketNotFoundError
from common.models.ticket import Ticket, TicketStatus
from common.schemas.request import (
    TicketCreateRequest,
    TicketEscalateRequest,
    TicketStatusUpdateRequest,
)
from common.schemas.response import TicketResponse
from dao.ticket_dao import TicketDAO


class TicketService:
    def __init__(self, dao: TicketDAO) -> None:
        self.dao = dao

    async def create_ticket(self, request: TicketCreateRequest) -> TicketResponse:
        ticket = Ticket(
            customer_id=request.customer_id,
            category=request.category,
            priority=request.priority,
            subject=request.subject,
            description=request.description,
            assigned_to=request.assigned_to,
        )
        ticket_id = await self.dao.insert(ticket)
        created = await self.dao.find_by_id(ticket_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def get_ticket(self, ticket_id: str) -> TicketResponse:
        ticket = await self.dao.find_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return self._to_response(ticket)

    async def list_tickets(self, customer_id: str) -> list[TicketResponse]:
        tickets = await self.dao.find_by_customer(customer_id)
        return [self._to_response(t) for t in tickets]

    async def update_status(
        self, ticket_id: str, request: TicketStatusUpdateRequest
    ) -> TicketResponse:
        ticket = await self.dao.find_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        if ticket.status == TicketStatus.CLOSED:
            raise TicketAlreadyClosedError(ticket_id)
        await self.dao.update_status(ticket_id, request.status, request.resolution)
        updated = await self.dao.find_by_id(ticket_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    async def escalate_ticket(
        self, ticket_id: str, request: TicketEscalateRequest
    ) -> TicketResponse:
        ticket = await self.dao.find_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        if ticket.status == TicketStatus.CLOSED:
            raise TicketAlreadyClosedError(ticket_id)
        await self.dao.escalate(ticket_id, request.assigned_to)
        updated = await self.dao.find_by_id(ticket_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    def _to_response(self, ticket: Ticket) -> TicketResponse:
        return TicketResponse(
            id=str(ticket.id),
            customer_id=ticket.customer_id,
            category=ticket.category,
            priority=ticket.priority,
            status=ticket.status,
            subject=ticket.subject,
            description=ticket.description,
            assigned_to=ticket.assigned_to,
            resolution=ticket.resolution,
            escalated_at=ticket.escalated_at,
            resolved_at=ticket.resolved_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

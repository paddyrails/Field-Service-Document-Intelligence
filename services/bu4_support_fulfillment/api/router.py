from fastapi import APIRouter, Depends

from api.dependencies import get_ticket_service
from common.schemas.request import (
    TicketCreateRequest,
    TicketEscalateRequest,
    TicketStatusUpdateRequest,
)
from common.schemas.response import TicketResponse
from service.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreateRequest,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    return await service.create_ticket(body)


@router.get("/customer/{customer_id}", response_model=list[TicketResponse])
async def list_tickets(
    customer_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketResponse]:
    return await service.list_tickets(customer_id)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    return await service.get_ticket(ticket_id)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: str,
    body: TicketStatusUpdateRequest,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    return await service.update_status(ticket_id, body)


@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
async def escalate_ticket(
    ticket_id: str,
    body: TicketEscalateRequest,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    return await service.escalate_ticket(ticket_id, body)

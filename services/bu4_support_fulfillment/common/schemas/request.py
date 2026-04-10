from pydantic import BaseModel

from common.models.ticket import TicketCategory, TicketPriority, TicketStatus


class TicketCreateRequest(BaseModel):
    customer_id: str
    category: TicketCategory
    priority: TicketPriority
    subject: str
    description: str
    assigned_to: str | None = None


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus
    resolution: str | None = None


class TicketEscalateRequest(BaseModel):
    reason: str
    assigned_to: str | None = None

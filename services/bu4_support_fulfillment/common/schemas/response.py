from datetime import datetime

from pydantic import BaseModel

from common.models.ticket import TicketCategory, TicketPriority, TicketStatus


class TicketResponse(BaseModel):
    id: str
    customer_id: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    subject: str
    description: str
    assigned_to: str | None
    resolution: str | None
    escalated_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

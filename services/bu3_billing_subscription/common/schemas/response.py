from datetime import datetime

from pydantic import BaseModel

from common.models.invoice import InvoiceStatus
from common.models.subscription import SubscriptionPlan, SubscriptionStatus


class InvoiceResponse(BaseModel):
    id: str
    customer_id: str
    amount: float
    due_date: datetime
    status: InvoiceStatus
    description: str
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    start_date: datetime
    renewal_date: datetime
    monthly_fee: float
    created_at: datetime
    updated_at: datetime

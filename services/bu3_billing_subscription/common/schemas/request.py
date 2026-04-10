from datetime import datetime

from pydantic import BaseModel

from common.models.subscription import SubscriptionPlan, SubscriptionStatus


class InvoiceCreateRequest(BaseModel):
    customer_id: str
    amount: float
    due_date: datetime
    description: str = ""


class SubscriptionCreateRequest(BaseModel):
    customer_id: str
    plan: SubscriptionPlan
    start_date: datetime
    renewal_date: datetime
    monthly_fee: float


class SubscriptionUpdateRequest(BaseModel):
    plan: SubscriptionPlan
    status: SubscriptionStatus
    monthly_fee: float

from datetime import datetime

from pydantic import BaseModel

from common.models.contract import ContractStatus, ContractType
from common.models.visit import VisitStatus


class ContractResponse(BaseModel):
    id: str
    customer_id: str
    contract_type: ContractType
    status: ContractStatus
    start_date: datetime
    end_date: datetime
    value: float
    description: str
    created_at: datetime
    updated_at: datetime


class VisitResponse(BaseModel):
    id: str
    customer_id: str
    contract_id: str | None
    scheduled_at: datetime
    status: VisitStatus
    assigned_to: str
    notes: str
    created_at: datetime
    updated_at: datetime

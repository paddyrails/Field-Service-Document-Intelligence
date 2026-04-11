from datetime import datetime

from pydantic import BaseModel

from common.models.contract import ContractStatus, ContractType
from common.models.visit import VisitStatus


class ContractCreateRequest(BaseModel):
    customer_id: str
    contract_type: ContractType
    start_date: datetime
    end_date: datetime
    value: float
    description: str = ""


class VisitCreateRequest(BaseModel):
    customer_id: str
    contract_id: str | None = None
    scheduled_at: datetime
    assigned_to: str
    notes: str = ""


class VisitUpdateRequest(BaseModel):
    status: VisitStatus
    notes: str | None = None

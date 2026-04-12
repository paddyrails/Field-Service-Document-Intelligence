from datetime import datetime

from pydantic import BaseModel

from common.models.visit import ServiceType, VisitStatus


class VisitCreateRequest(BaseModel):
    patient_id: str
    patient_name: str
    service_type: ServiceType
    scheduled_at: datetime
    address: str | None = None
    assigned_to: str | None = None
    notes: str | None = None


class VisitStatusUpdateRequest(BaseModel):
    status: VisitStatus


class VisitClaimRequest(BaseModel):
    slack_user_id: str


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    service_type: ServiceType | None = None

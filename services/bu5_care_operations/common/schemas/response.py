from datetime import datetime

from pydantic import BaseModel

from common.models.visit import ServiceType, VisitStatus


class VisitResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    service_type: ServiceType
    scheduled_at: datetime
    address: str | None
    assigned_to: str | None
    appointment_id: str | None
    notes: str | None
    status: VisitStatus
    created_at: datetime
    updated_at: datetime


class ClaimVisitResponse(BaseModel):
    visit: VisitResponse
    care_instructions: list[str]


class RAGSearchResponse(BaseModel):
    results: list[dict]

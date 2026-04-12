from datetime import datetime

from pydantic import BaseModel


class AppointmentCreateRequest(BaseModel):
    patient_id: str
    patient_name: str
    service_type: str   # e.g. "skilled-nursing", "physical-therapy"
    scheduled_at: datetime
    address: str | None = None
    notes: str | None = None

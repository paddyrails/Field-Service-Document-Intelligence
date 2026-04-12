from datetime import datetime

from pydantic import BaseModel


class AppointmentCreateResponse(BaseModel):
    appointment_id: str
    patient_id: str
    patient_name: str
    service_type: str
    scheduled_at: datetime
    address: str | None
    notes: str | None
    status: str = "booked"

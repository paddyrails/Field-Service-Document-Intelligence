import uuid

from fastapi import APIRouter

from common.kafka.producer import get_producer
from common.schemas.request import AppointmentCreateRequest
from common.schemas.response import AppointmentCreateResponse

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentCreateResponse, status_code=201)
async def create_appointment(body: AppointmentCreateRequest) -> AppointmentCreateResponse:
    """Book an appointment and publish an event to Kafka for care operations to consume."""
    appointment_id = str(uuid.uuid4())
    event = {
        "appointment_id": appointment_id,
        "patient_id": body.patient_id,
        "patient_name": body.patient_name,
        "service_type": body.service_type,
        "scheduled_at": body.scheduled_at.isoformat(),
        "address": body.address,
        "notes": body.notes,
    }
    producer = await get_producer()
    await producer.send_and_wait("appointment.booked", event)

    return AppointmentCreateResponse(**event, status="booked")

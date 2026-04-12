from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class ServiceType(str, Enum):
    PERSONAL_CARE_COMPANIONSHIP = "personal-care-companionship"
    SKILLED_NURSING = "skilled-nursing"
    PHYSICAL_THERAPY = "physical-therapy"
    OCCUPATIONAL_THERAPY = "occupational-therapy"
    RESPITE_CARE = "respite-care"


class VisitStatus(str, Enum):
    PENDING = "pending"          # created from Kafka event, not yet claimed
    SCHEDULED = "scheduled"      # claimed by a field officer
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Visit(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    patient_id: str
    patient_name: str
    service_type: ServiceType
    scheduled_at: datetime
    address: str | None = None
    assigned_to: str | None = None    # None until claimed
    appointment_id: str | None = None  # source appointment reference
    notes: str | None = None
    status: VisitStatus = VisitStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_mongo(cls, data: dict) -> "Visit":
        return cls.model_validate(data)

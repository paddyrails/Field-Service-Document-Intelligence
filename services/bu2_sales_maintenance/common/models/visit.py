from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class VisitStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Visit(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    customer_id: str
    contract_id: str | None = None
    scheduled_at: datetime
    status: VisitStatus = VisitStatus.SCHEDULED
    assigned_to: str
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_mongo(cls, doc: dict) -> "Visit":
        return cls(**doc)

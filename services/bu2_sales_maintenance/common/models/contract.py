from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class ContractType(str, Enum):
    SERVICE = "service"
    MAINTENANCE = "maintenance"
    WARRANTY = "warranty"


class ContractStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Contract(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    customer_id: str
    contract_type: ContractType
    status: ContractStatus = ContractStatus.PENDING
    start_date: datetime
    end_date: datetime
    value: float
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_mongo(cls, doc: dict) -> "Contract":
        return cls(**doc)

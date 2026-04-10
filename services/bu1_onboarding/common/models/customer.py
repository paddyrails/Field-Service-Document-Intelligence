from datetime import datetime, timezone
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

class KYCStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"

class OnboardingStage(str, Enum):
    REGISTERED = "registered"
    KYC_SUBMITTED = "kyc_submitted"
    KYC_VERIFIED = "kyc_verified"
    COMPLETED = "completed"

class Customer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    id: ObjectId | None = Field(default=None, alias="_id")
    name: str
    email:str
    phone: str
    address: str
    kyc_status: KYCStatus = KYCStatus.PENDING
    kyc_notes: str = ""
    onboarding_stage: OnboardingStage = OnboardingStage.REGISTERED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
    
    @classmethod
    def from_mongo(cls, data: dict) -> "Customer":
        return cls.model_validate(data)


from datetime import datetime

from pydantic import BaseModel

from common.models.customer import KYCStatus, OnboardingStage

class CustomerResponse(BaseModel):
    id: str
    name: str
    email:str
    phone: str
    address:str
    kyc_status: KYCStatus
    kyc_notes: str
    onboarding_stage: OnboardingStage
    created_at: datetime
    updated_at: datetime

class OnBoardingStatusResponse(BaseModel):
    customer_id: str
    onboarding_stage: OnboardingStage
    kyc_status: KYCStatus
    is_complete: bool
    
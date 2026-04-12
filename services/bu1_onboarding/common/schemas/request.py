from pydantic import BaseModel, EmailStr

from common.models.customer import KYCStatus

class CustomerCreateRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str

class KYCUpdateRequest(BaseModel):
    kyc_status: KYCStatus
    kyc_notes: str = ""

class IngestRequest(BaseModel):
    folder_path: str
    metadata: dict = {}
    
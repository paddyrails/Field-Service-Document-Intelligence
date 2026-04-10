from fastapi import APIRouter, Depends

from api.dependencies import get_customer_service
from common.schemas.request import CustomerCreateRequest, KYCUpdateRequest
from common.schemas.response import CustomerResponse, OnBoardingStatusResponse
from service.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
async def register_customer(
    body: CustomerCreateRequest,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return await service.register_customer(body)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return await service.get_customer(customer_id)


@router.patch("/{customer_id}/kyc", response_model=CustomerResponse)
async def update_kyc(
    customer_id: str,
    body: KYCUpdateRequest,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return await service.update_kyc(customer_id, body)


@router.get("/{customer_id}/onboarding-status", response_model=OnBoardingStatusResponse)
async def get_onboarding_status(
    customer_id: str,
    service: CustomerService = Depends(get_customer_service),
) -> OnBoardingStatusResponse:
    return await service.get_onboarding_status(customer_id)
from common.exceptions.handlers import CustomerNotFoundError, DuplicateCustomerError
from common.models.customer import Customer, KYCStatus, OnboardingStage
from common.schemas.request import CustomerCreateRequest, KYCUpdateRequest
from common.schemas.response import CustomerResponse, OnBoardingStatusResponse
from dao.customer_dao import CustomerDAO


class CustomerService:
    def __init__(self, dao: CustomerDAO) -> None:
        self.dao = dao

    async def register_customer(self, request: CustomerCreateRequest) -> CustomerResponse:
        existing = await self.dao.find_by_email(request.email)
        if existing:
            raise DuplicateCustomerError(request.email)
        
        customer = Customer(
            name=request.name,
            email=request.email,
            phone=request.phone,
            address=request.address
        )
        customer_id = await self.dao.insert(customer)
        customer.id = None
        created = await self.dao.find_by_id(customer_id)
        return self._to_response(created)
    
    async def get_customer(self, customer_id: str) -> CustomerResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return self._to_response(customer)

    async def update_kyc(self, customer_id: str, request: KYCUpdateRequest) -> CustomerResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        await self.dao.update_kyc(customer_id, request.kyc_status, request.kyc_notes)

        if request.kyc_status == KYCStatus.APPROVED:
            await self.dao.update_onboarding_stage(customer_id, OnboardingStage.KYC_VERIFIED)

        updated = await self.dao.find_by_id(customer_id)
        return self._to_response(updated)

    async def get_onboarding_status(self, customer_id: str) -> OnBoardingStatusResponse:
        customer = await self.dao.find_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)

        return OnBoardingStatusResponse(
            customer_id=customer_id,
            onboarding_stage=customer.onboarding_stage,
            kyc_status=customer.kyc_status,
            is_complete=customer.onboarding_stage == OnboardingStage.COMPLETED,
        )

    def _to_response(self, customer: Customer) -> CustomerResponse:
        return CustomerResponse(
            id=str(customer.id),
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            address=customer.address,
            kyc_status=customer.kyc_status,
            kyc_notes=customer.kyc_notes,
            onboarding_stage=customer.onboarding_stage,
            created_at=customer.created_at,
            updated_at=customer.updated_at

        )
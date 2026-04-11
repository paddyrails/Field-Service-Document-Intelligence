from fastapi import APIRouter, Depends

from api.dependencies import get_contract_service, get_visit_service
from common.schemas.request import ContractCreateRequest, VisitCreateRequest, VisitUpdateRequest
from common.schemas.response import ContractResponse, VisitResponse
from service.contract_service import ContractService
from service.visit_service import VisitService

contract_router = APIRouter(prefix="/contracts", tags=["contracts"])
visit_router = APIRouter(prefix="/visits", tags=["visits"])


@contract_router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(
    body: ContractCreateRequest,
    service: ContractService = Depends(get_contract_service),
) -> ContractResponse:
    return await service.create_contract(body)


@contract_router.get("/customer/{customer_id}", response_model=list[ContractResponse])
async def list_contracts(
    customer_id: str,
    service: ContractService = Depends(get_contract_service),
) -> list[ContractResponse]:
    return await service.list_contracts(customer_id)


@contract_router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    service: ContractService = Depends(get_contract_service),
) -> ContractResponse:
    return await service.get_contract(contract_id)


@visit_router.post("", response_model=VisitResponse, status_code=201)
async def schedule_visit(
    body: VisitCreateRequest,
    service: VisitService = Depends(get_visit_service),
) -> VisitResponse:
    return await service.schedule_visit(body)


@visit_router.get("/customer/{customer_id}", response_model=list[VisitResponse])
async def list_visits(
    customer_id: str,
    service: VisitService = Depends(get_visit_service),
) -> list[VisitResponse]:
    return await service.list_visits(customer_id)


@visit_router.patch("/{visit_id}", response_model=VisitResponse)
async def update_visit(
    visit_id: str,
    body: VisitUpdateRequest,
    service: VisitService = Depends(get_visit_service),
) -> VisitResponse:
    return await service.update_visit(visit_id, body)

from common.exceptions.handlers import ContractNotFoundError
from common.models.contract import Contract
from common.schemas.request import ContractCreateRequest
from common.schemas.response import ContractResponse
from dao.contract_dao import ContractDAO


class ContractService:
    def __init__(self, dao: ContractDAO) -> None:
        self.dao = dao

    async def create_contract(self, request: ContractCreateRequest) -> ContractResponse:
        contract = Contract(
            customer_id=request.customer_id,
            contract_type=request.contract_type,
            start_date=request.start_date,
            end_date=request.end_date,
            value=request.value,
            description=request.description,
        )
        contract_id = await self.dao.insert(contract)
        created = await self.dao.find_by_id(contract_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def get_contract(self, contract_id: str) -> ContractResponse:
        contract = await self.dao.find_by_id(contract_id)
        if contract is None:
            raise ContractNotFoundError(contract_id)
        return self._to_response(contract)

    async def list_contracts(self, customer_id: str) -> list[ContractResponse]:
        contracts = await self.dao.find_by_customer(customer_id)
        return [self._to_response(c) for c in contracts]

    def _to_response(self, contract: Contract) -> ContractResponse:
        return ContractResponse(
            id=str(contract.id),
            customer_id=contract.customer_id,
            contract_type=contract.contract_type,
            status=contract.status,
            start_date=contract.start_date,
            end_date=contract.end_date,
            value=contract.value,
            description=contract.description,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
        )

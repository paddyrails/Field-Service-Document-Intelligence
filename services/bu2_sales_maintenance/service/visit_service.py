from common.exceptions.handlers import VisitNotFoundError
from common.models.visit import Visit
from common.schemas.request import VisitCreateRequest, VisitUpdateRequest
from common.schemas.response import VisitResponse
from dao.visit_dao import VisitDAO


class VisitService:
    def __init__(self, dao: VisitDAO) -> None:
        self.dao = dao

    async def schedule_visit(self, request: VisitCreateRequest) -> VisitResponse:
        visit = Visit(
            customer_id=request.customer_id,
            contract_id=request.contract_id,
            scheduled_at=request.scheduled_at,
            assigned_to=request.assigned_to,
            notes=request.notes,
        )
        visit_id = await self.dao.insert(visit)
        created = await self.dao.find_by_id(visit_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def list_visits(self, customer_id: str) -> list[VisitResponse]:
        visits = await self.dao.find_by_customer(customer_id)
        return [self._to_response(v) for v in visits]

    async def update_visit(self, visit_id: str, request: VisitUpdateRequest) -> VisitResponse:
        visit = await self.dao.find_by_id(visit_id)
        if visit is None:
            raise VisitNotFoundError(visit_id)
        await self.dao.update(visit_id, request.status, request.notes)
        updated = await self.dao.find_by_id(visit_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    def _to_response(self, visit: Visit) -> VisitResponse:
        return VisitResponse(
            id=str(visit.id),
            customer_id=visit.customer_id,
            contract_id=visit.contract_id,
            scheduled_at=visit.scheduled_at,
            status=visit.status,
            assigned_to=visit.assigned_to,
            notes=visit.notes,
            created_at=visit.created_at,
            updated_at=visit.updated_at,
        )

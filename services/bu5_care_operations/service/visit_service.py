import logging
from datetime import datetime

import httpx

from common.config import settings
from common.exceptions.handlers import VisitNotFoundError

logger = logging.getLogger(__name__)
from common.models.visit import ServiceType, Visit, VisitStatus
from common.schemas.request import RAGSearchRequest, VisitClaimRequest, VisitCreateRequest, VisitStatusUpdateRequest
from common.schemas.response import ClaimVisitResponse, RAGSearchResponse, VisitResponse
from common.slack.notifier import SlackNotifier
from dao.vector_dao import VectorDAO
from dao.visit_dao import VisitDAO


class VisitService:
    def __init__(
        self,
        visit_dao: VisitDAO,
        vector_dao: VectorDAO,
        slack_notifier: SlackNotifier | None = None,
    ) -> None:
        self.visit_dao = visit_dao
        self.vector_dao = vector_dao
        self.slack_notifier = slack_notifier

    async def create_visit(self, request: VisitCreateRequest) -> VisitResponse:
        visit = Visit(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            service_type=request.service_type,
            scheduled_at=request.scheduled_at,
            address=request.address,
            assigned_to=request.assigned_to,
            notes=request.notes,
        )
        visit_id = await self.visit_dao.insert(visit)
        created = await self.visit_dao.find_by_id(visit_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def get_visit(self, visit_id: str) -> VisitResponse:
        visit = await self.visit_dao.find_by_id(visit_id)
        if visit is None:
            raise VisitNotFoundError(visit_id)
        return self._to_response(visit)

    async def list_visits(self, patient_id: str) -> list[VisitResponse]:
        visits = await self.visit_dao.find_by_patient(patient_id)
        return [self._to_response(v) for v in visits]

    async def update_status(self, visit_id: str, request: VisitStatusUpdateRequest) -> VisitResponse:
        visit = await self.visit_dao.find_by_id(visit_id)
        if visit is None:
            raise VisitNotFoundError(visit_id)
        await self.visit_dao.update_status(visit_id, request.status)
        updated = await self.visit_dao.find_by_id(visit_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    async def search_docs(self, request: RAGSearchRequest) -> RAGSearchResponse:
        results = await self.vector_dao.search(
            query=request.query,
            top_k=request.top_k,
            service_type=request.service_type.value if request.service_type else None,
        )
        return RAGSearchResponse(results=results)

    async def handle_appointment_event(self, event: dict) -> None:
        """Called by the Kafka consumer for each appointment.booked event."""
        visit = Visit(
            patient_id=event["patient_id"],
            patient_name=event["patient_name"],
            service_type=ServiceType(event["service_type"]),
            scheduled_at=datetime.fromisoformat(event["scheduled_at"]),
            address=event.get("address"),
            notes=event.get("notes"),
            appointment_id=event.get("appointment_id"),
            status=VisitStatus.PENDING,
        )
        visit_id = await self.visit_dao.insert(visit)

        if self.slack_notifier:
            await self.slack_notifier.post_pending_visit(
                visit_id=visit_id,
                patient_name=event["patient_name"],
                service_type=event["service_type"],
                scheduled_at=visit.scheduled_at,
                address=event.get("address"),
            )

    async def claim_visit(self, visit_id: str, request: VisitClaimRequest) -> ClaimVisitResponse:
        """Assign a pending visit to a field officer and return care instructions via Agent."""
        visit = await self.visit_dao.find_by_id(visit_id)
        if visit is None:
            raise VisitNotFoundError(visit_id)

        await self.visit_dao.assign_visit(visit_id, request.slack_user_id)
        updated = await self.visit_dao.find_by_id(visit_id)

        service_type = updated.service_type.value  # type: ignore[union-attr]
        query = (
            f"What are the preparation checklist and requirements for a "
            f"{service_type} home visit for patient {updated.patient_name}?"  # type: ignore[union-attr]
            f" Include what supplies, equipment, and documentation to bring."
        )

        care_instructions = await self._fetch_agent_instructions(
            query=query,
            session_id=f"visit-claim-{visit_id}",
            user_id=request.slack_user_id,
        )

        return ClaimVisitResponse(
            visit=self._to_response(updated),  # type: ignore[arg-type]
            care_instructions=care_instructions,
        )

    async def _fetch_agent_instructions(
        self, query: str, session_id: str, user_id: str
    ) -> list[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.agent_base_url}/query",
                    json={
                        "query": query,
                        "session_id": session_id,
                        "channel": "care-operations",
                        "user_id": user_id,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                agent_reply = response.json().get("response", "")
                return [agent_reply] if agent_reply else []
        except Exception as e:
            logger.error(f"Agent API call failed for visit claim: {e}")
            return []

    def _to_response(self, visit: Visit) -> VisitResponse:
        return VisitResponse(
            id=str(visit.id),
            patient_id=visit.patient_id,
            patient_name=visit.patient_name,
            service_type=visit.service_type,
            scheduled_at=visit.scheduled_at,
            address=visit.address,
            assigned_to=visit.assigned_to,
            appointment_id=visit.appointment_id,
            notes=visit.notes,
            status=visit.status,
            created_at=visit.created_at,
            updated_at=visit.updated_at,
        )

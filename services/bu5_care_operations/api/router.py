from fastapi import APIRouter, Depends

from api.dependencies import get_visit_service
from common.schemas.request import RAGSearchRequest, VisitClaimRequest, VisitCreateRequest, VisitStatusUpdateRequest
from common.schemas.response import ClaimVisitResponse, RAGSearchResponse, VisitResponse
from service.visit_service import VisitService

router = APIRouter()

visit_router = APIRouter(prefix="/visits", tags=["visits"])
rag_router = APIRouter(prefix="/rag", tags=["rag"])


# ── Visit CRUD ────────────────────────────────────────────────────────────────

@visit_router.post("", response_model=VisitResponse, status_code=201)
async def create_visit(
    body: VisitCreateRequest,
    service: VisitService = Depends(get_visit_service),
) -> VisitResponse:
    return await service.create_visit(body)


@visit_router.get("/patient/{patient_id}", response_model=list[VisitResponse])
async def list_visits(
    patient_id: str,
    service: VisitService = Depends(get_visit_service),
) -> list[VisitResponse]:
    return await service.list_visits(patient_id)


@visit_router.get("/{visit_id}", response_model=VisitResponse)
async def get_visit(
    visit_id: str,
    service: VisitService = Depends(get_visit_service),
) -> VisitResponse:
    return await service.get_visit(visit_id)


@visit_router.patch("/{visit_id}/status", response_model=VisitResponse)
async def update_visit_status(
    visit_id: str,
    body: VisitStatusUpdateRequest,
    service: VisitService = Depends(get_visit_service),
) -> VisitResponse:
    return await service.update_status(visit_id, body)


@visit_router.patch("/{visit_id}/claim", response_model=ClaimVisitResponse)
async def claim_visit(
    visit_id: str,
    body: VisitClaimRequest,
    service: VisitService = Depends(get_visit_service),
) -> ClaimVisitResponse:
    return await service.claim_visit(visit_id, body)


# ── RAG ───────────────────────────────────────────────────────────────────────

@rag_router.post("/search", response_model=RAGSearchResponse)
async def search_docs(
    body: RAGSearchRequest,
    service: VisitService = Depends(get_visit_service),
) -> RAGSearchResponse:
    return await service.search_docs(body)


router.include_router(visit_router)
router.include_router(rag_router)

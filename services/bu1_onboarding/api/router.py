import openai
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_customer_service
from common.config import settings
from common.schemas.request import CustomerCreateRequest, IngestRequest, KYCUpdateRequest
from common.schemas.response import CustomerResponse, OnBoardingStatusResponse
from service.customer_service import CustomerService

# ── Customer routes ───────────────────────────────────────────────────────────

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


# ── Ingestion + RAG routes ────────────────────────────────────────────────────
# Separate router — not under /customers prefix

ingest_router = APIRouter(tags=["ingestion"])


@ingest_router.post("/ingest")
async def ingest_folder(
    body: IngestRequest,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    """
    Ingest all .pdf, .txt and .md files from a mounted folder into the
    BU1 vector store.
    Body: { "folder_path": "/docs/bu1", "metadata": {} }
    """
    try:
        return await service.ingest_folder(body)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@ingest_router.post("/rag/search")
async def rag_search(
    body: dict,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    """
    Semantic search over BU1 document chunks.
    Body: { "query": "...", "top_k": 5, "filter": {} }
    """
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query field is required")

    top_k = body.get("top_k", settings.rag_top_k)
    filters = body.get("filter")

    _openai = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await _openai.embeddings.create(
        model=settings.openai_embedding_model,
        input=query,
    )
    query_vector = response.data[0].embedding

    results = await service.rag_search(query_vector, top_k=top_k, filters=filters)
    return {"results": results}

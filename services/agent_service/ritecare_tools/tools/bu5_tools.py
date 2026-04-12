import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0,
    api_key=settings.openai_api_key,
)

_BASE_URL = settings.bu5_base_url

_SERVICE_TYPES = (
    "personal-care-companionship",
    "skilled-nursing",
    "physical-therapy",
    "occupational-therapy",
    "respite-care",
)


async def _extract_visit_id(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Extract the visit ID from the user query. "
            "Visit IDs are alphanumeric strings or MongoDB ObjectIds. "
            "Reply with ONLY the visit ID and nothing else. "
            "If no visit ID is present, reply with: NONE"
        )),
        HumanMessage(content=query),
    ])
    result = response.content.strip()
    return None if result == "NONE" else result


async def _extract_patient_id(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Extract the patient ID from the user query. "
            "Patient IDs are alphanumeric strings or MongoDB ObjectIds. "
            "Reply with ONLY the patient ID and nothing else. "
            "If no patient ID is present, reply with: NONE"
        )),
        HumanMessage(content=query),
    ])
    result = response.content.strip()
    return None if result == "NONE" else result


async def _extract_service_type(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Identify if the user query mentions a specific care service type. "
            f"Valid service types are: {', '.join(_SERVICE_TYPES)}. "
            "Reply with ONLY the matching service type exactly as listed above. "
            "If no service type is mentioned, reply with: NONE"
        )),
        HumanMessage(content=query),
    ])
    result = response.content.strip()
    return None if result == "NONE" else result


async def get_visit_by_id(query: str) -> dict:
    """
    CRUD tool — fetches a patient visit from BU5 by visit ID.
    """
    visit_id = await _extract_visit_id(query)
    if not visit_id:
        return {"error": "Could not extract visit ID from query"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/visits/{visit_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return {"error": f"Visit '{visit_id}' not found"}
        response.raise_for_status()
        return response.json()


async def list_patient_visits(query: str) -> list[dict]:
    """
    CRUD tool — lists all visits for a patient from BU5.
    """
    patient_id = await _extract_patient_id(query)
    if not patient_id:
        return [{"error": "Could not extract patient ID from query"}]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/visits/patient/{patient_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def search_care_documents(query: str) -> list[str]:
    """
    RAG tool — searches BU5 care operations documents.
    Optionally filters by service type if mentioned in the query.
    """
    service_type = await _extract_service_type(query)

    payload: dict = {"query": query, "top_k": settings.rag_top_k}
    if service_type:
        payload["service_type"] = service_type

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/rag/search",
            json=payload,
            timeout=15.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [chunk["text"] for chunk in data.get("results", [])]

import httpx

from shared.config import settings

_BASE_URL = settings.bu5_base_url

_SERVICE_TYPES = (
    "personal-care-companionship",
    "skilled-nursing",
    "physical-therapy",
    "occupational-therapy",
    "respite-care",
)


def _find_service_type(query: str) -> str | None:
    """Direct string match — faster and more reliable than an LLM call."""
    query_lower = query.lower()
    for st in _SERVICE_TYPES:
        if st in query_lower:
            return st
    return None


async def get_visit_by_id(visit_id: str) -> dict:
    """
    CRUD tool — fetches a patient visit from BU5 by visit ID.

    Args:
        visit_id: The visit ID to look up (e.g. V789 or a MongoDB ObjectId)

    Returns:
        Visit record with patient name, service type, status, scheduled time
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/visits/{visit_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return {"error": f"Visit '{visit_id}' not found"}
        response.raise_for_status()
        return response.json()


async def list_patient_visits(patient_id: str) -> list[dict]:
    """
    CRUD tool — lists all visits for a patient from BU5.

    Args:
        patient_id: The patient ID to look up

    Returns:
        List of visit records for the patient
    """
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
    service_type = _find_service_type(query)

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

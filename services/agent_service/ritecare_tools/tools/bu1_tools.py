from shared.config import settings
from shared.http_client import resilient_request

_BASE_URL = settings.bu1_base_url


async def get_customer_by_id(customer_id: str) -> dict:
    """
    Fetches customer details by ID from BU1 onboarding service.
    """
    resp = await resilient_request("GET", f"{_BASE_URL}/customers/{customer_id}", "bu1")
    return resp.json()


async def get_onboarding_status(customer_id: str) -> dict:
    """
    CRUD tool - fetches the onboarding status for a customer from BU1.
    """
    resp = await resilient_request("GET", f"{_BASE_URL}/customers/{customer_id}/onboarding-status", "bu1")
    return resp.json()


async def search_onboarding_docs(query: str) -> list[str]:
    """RAG tool - semantic search over BU1 onboarding documents, which has insurance information"""
    resp = await resilient_request(
        "POST", f"{_BASE_URL}/rag/search", "bu1",
        json={"query": query, "top_k": settings.rag_top_k},
    )
    return [chunk["text"] for chunk in resp.json().get("results", [])]

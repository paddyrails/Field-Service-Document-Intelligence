import httpx
from shared.config import settings

_BASE_URL = settings.bu4_base_url


async def get_ticket_by_id(ticket_id: str) -> dict:
    """
    CRUD tool — fetches a support ticket from BU4 by ticket ID.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/tickets/{ticket_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return {"error": f"Ticket '{ticket_id}' not found"}
        response.raise_for_status()
        return response.json()


async def list_tickets(customer_id: str) -> list[dict]:
    """
    CRUD tool — lists all tickets for a customer from BU4.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/tickets/customer/{customer_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def search_knowledge_base(query: str) -> list[str]:
    """
    RAG tool — semantic search over BU4 knowledge base articles.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/rag/search",
            json={"query": query, "top_k": settings.rag_top_k},
            timeout=15.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [chunk["text"] for chunk in data.get("results", [])]


async def search_resolved_tickets(query: str) -> list[str]:
    """
    RAG tool — semantic search over BU4 resolved tickets.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/rag/search",
            json={
                "query": query,
                "top_k": settings.rag_top_k,
                "filter": {"type": "resolved_ticket"},
            },
            timeout=15.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [chunk["text"] for chunk in data.get("results", [])]

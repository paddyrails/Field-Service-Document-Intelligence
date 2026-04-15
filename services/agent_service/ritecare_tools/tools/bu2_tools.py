import httpx

from shared.config import settings


_BASE_URL = settings.bu2_base_url


async def get_contract_by_id(contract_id:str) -> dict:
    """
    CRUD tool - fetches a service contract from BU2 by contract ID
    """   
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/contracts/{contract_id}",
            timeout=10.0
        )
        if response.status_code == 404:
            return {"error": f"Contract '{contract_id}' not found"}
        response.raise_for_status()
        return response.json()
    
async def list_contracts(customer_id: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/contracts/customer/{customer_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def list_visits(customer_id: str) -> list[dict]:

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/visits/customer/{customer_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def search_service_manuals(query: str) -> list[str]:
    """
    RAG tool - semantic search over BU2 service manuals and field guides
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/rag/search",
            json={"query": query, "top_k": settings.rag_top_k},
            timeout=15.0
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [chunk["text"] for chunk in data.get("results", [])]

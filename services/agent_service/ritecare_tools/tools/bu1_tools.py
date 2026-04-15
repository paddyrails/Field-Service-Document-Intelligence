import httpx
import asyncio

from shared.config import settings

_BASE_URL = settings.bu1_base_url


async def get_customer_by_id(customer_id: str) -> dict:
    """
    Fetches customer details by ID from BU1 onbaording service.
    Args: customer_id: the customer ID to look up
    Returns: Customer record with name, KYC status, onboarding progress    
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/customers/{customer_id}",
            timeout=10.0
        )
        if response.status_code == 404:
            return {"error": f"Customer '{customer_id}' not found"}
        response.raise_for_status()
        return response.json()
    

async def get_onboarding_status(customer_id: str) -> dict:
    """
    CRUD tool - fetches th onboarding status for a customer from BU1
    """    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/customers/{customer_id}/onboarding-status",
            timeout=10.0
        )
        if(response.status_code == 404):
            return {"error": f"Customer '{customer_id}' not found"}
        response.raise_for_status()
        return response.json()
    

async def search_onboarding_docs(query:str) -> list[str]:
    """
    RAG tool - semantic search over BU1 onboarding documents.
    Returns a list of relevant text chunks
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
        return [chunk["text"] for chunk in data.get("results",[])]

    

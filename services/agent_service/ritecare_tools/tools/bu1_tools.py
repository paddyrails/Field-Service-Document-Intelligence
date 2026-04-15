import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.config import settings
from shared.circuit import bu1_breaker

from shared.http_client import resilient_request

_BASE_URL = settings.bu1_base_url

async def get_customer_by_id(customer_id: str) -> dict:
    """
    Fetches customer details by ID from BU1 onboarding service.
    """
    resp = await resilient_request("GET", f"{_BASE_URL}/customers/{customer_id}", "bu1")
    return resp.json


# @bu1_breaker
# @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=1, max=5),
#         retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout))
# )
# async def get_customer_by_id(customer_id: str) -> dict:
#     """
#     Fetches customer details by ID from BU1 onbaording service.
#     Args: customer_id: the customer ID to look up
#     Returns: Customer record with name, KYC status, onboarding progress    
#     """
    
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             f"{_BASE_URL}/customers/{customer_id}",
#             timeout=10.0
#         )
#         if response.status_code == 404:
#             return {"error": f"Customer '{customer_id}' not found"}
#         response.raise_for_status()
#         return response.json()
    

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



async def search_onboarding_docs(query: str) -> list[str]:
    """RAG tool - semantic search over BU1 onboarding documents"""
    resp = await resilient_request(
        "POST", f"{_BASE_URL}/rag/search", "bu1",
        json={"query": query, "top_k": settings.rag_top_k}
    )
    return [chunk["text"] for chunk in resp.json().get("results", [])]

# async def search_onboarding_docs(query:str) -> list[str]:
#     """
#     RAG tool - semantic search over BU1 onboarding documents.
#     Returns a list of relevant text chunks
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{_BASE_URL}/rag/search",
#             json={"query": query, "top_k": settings.rag_top_k},
#             timeout=15.0
#         )
#         if response.status_code == 404:
#             return []
        
#         response.raise_for_status()
#         data = response.json()
#         return [chunk["text"] for chunk in data.get("results",[])]

    

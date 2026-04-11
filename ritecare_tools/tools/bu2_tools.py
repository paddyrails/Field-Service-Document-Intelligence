import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0,
    api_key=settings.openai_api_key
)

_BASE_URL = settings.bu2_base_url

async def _extract_customer_id(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Extract the customer ID from the user query. "
              "Customer IDs are alphanumeric strings like 'C123','CUST-001', or a MongoDB ObjectId. "
              "Reply with ONLY the customer ID and nothing else. "
              "If no customer ID is present, reply with: NONE"
        )),
        HumanMessage(content=query),
    ])
    result = response.content.strip()
    return None if result == "None" else result

async def _extract_contract_id(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Extract the contract ID from the user query. "
              "Contract IDs are alphanumeric strings like 'CON124312','CONTRACT-001', or a MongoDB ObjectId. "
              "Reply with ONLY the contract ID and nothing else. "
              "If no contract ID is present, reply with: NONE"
        )),
        HumanMessage(content=query),
    ])
    result = response.content.strip()
    return None if result == "None" else result

async def get_contract_by_id(query:str) -> dict:
    """
    CRUD tool - fetches a service contract from BU2 by contract ID
    """
    contract_id = await _extract_contract_id(query)
    if not contract_id:
        return {"error": "Could not extract contract ID from query"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/contracts/{contract_id}",
            timeout=10.0
        )
        if response.status_code == 404:
            return {"error": f"Contract '{contract_id}' not found"}
        response.raise_for_status()
        return response.json()
    
async def list_contracts(query: str) -> list[dict]:
    """
    CRUD tool — lists all contracts for a customer from BU2.
    """
    customer_id = await _extract_customer_id(query)
    if not customer_id:
        return [{"error": "Could not extract customer ID from query"}]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/contracts/customer/{customer_id}",
            timeout=10.0,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()


async def list_visits(query: str) -> list[dict]:
    """
    CRUD tool — lists all field visits for a customer from BU2.
    """
    customer_id = await _extract_customer_id(query)
    if not customer_id:
        return [{"error": "Could not extract customer ID from query"}]

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

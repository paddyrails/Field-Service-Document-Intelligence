import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0,
    api_key=settings.openai_api_key
)

_BASE_URL = settings.bu1_base_url

async def _extract_customer_id(query: str) -> str | None:
    """
    Uses the LLM to extract a customer ID from the user query.
    Returns None if no customer ID is found.
    """
    response = await _llm.ainvoke([
        SystemMessage(content=(
            "Extract the customer ID from the user query. "
            "Customer IDs are alphanumeric string line 'C123', 'CUST-001' or a MongoDB ObjectId"
            "Reply with ONLY the customer ID and nothing else. "
            "if no customer ID is present, reply with: NONE"
        )),
        HumanMessage(content=query)
    ])

    result = response.content.strip()
    return None if result == "None" else result

async def get_customer_by_id(query: str) -> dict:
    """
    CRUD tool -fetches a customer profile form BU1 by customer iD    
    """
    customer_id = await _extract_customer_id(query)

    if not customer_id:
        return {"error": "Could not extract customer ID from query"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/customers/{customer_id}",
            timeout=10.0
        )
        if response.status_code == 404:
            return {"error": f"Customer '{customer_id}' not found"}
        response.raise_for_status()
        return response.json()
    

async def get_onboarding_status(query: str) -> dict:
    """
    CRUD tool - fetches th onboarding status for a customer from BU1
    """
    customer_id = await _extract_customer_id(query)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/customers/{customer_id}/onboarding-status",
            timeout=10.0
        )
        if(response.status_code == 404):
            return {"error": f"Customer '{customer_id} not found"}
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

    

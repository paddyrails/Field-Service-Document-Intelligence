import httpx                                              
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI     
                                        
from shared.config import settings
                                                                    
_llm = ChatOpenAI(
    model=settings.openai_chat_model,                                
    temperature=0,                                        
    api_key=settings.openai_api_key,           
)                                           
                                        
_BASE_URL = settings.bu4_base_url
                                                                    

async def _extract_customer_id(query: str) -> str | None:            
    response = await _llm.ainvoke([                       
        SystemMessage(content=(                
            "Extract the customer ID from the user query. "
            "Customer IDs are alphanumeric strings like 'C123', 'CUST-001', or a MongoDB ObjectId. "
            "Reply with ONLY the customer ID and nothing else. "     
            "If no customer ID is present, reply with: NONE"
        )),                                                          
        HumanMessage(content=query),                      
    ])                                         
    result = response.content.strip()                                
    return None if result == "NONE" else result
                                                                    
                                                        
async def _extract_ticket_id(query: str) -> str | None:
    response = await _llm.ainvoke([
        SystemMessage(content=(                                      
            "Extract the ticket ID from the user query. "
            "Ticket IDs are alphanumeric strings like 'T99','TICKET-001', or a MongoDB ObjectId. "                    
            "Reply with ONLY the ticket ID and nothing else. "
            "If no ticket ID is present, reply with: NONE"
        )),                                                          
        HumanMessage(content=query),        
    ])                                                               
    result = response.content.strip()                     
    return None if result == "NONE" else result                      

                                                                    
async def get_ticket_by_id(query: str) -> dict:           
    """                                        
    CRUD tool — fetches a support ticket from BU4 by ticket ID.      
    """
    ticket_id = await _extract_ticket_id(query)                      
    if not ticket_id:                                     
        return {"error": "Could not extract ticket ID from query"}
                                            
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/tickets/{ticket_id}",                      
            timeout=10.0,
        )                                                            
        if response.status_code == 404:                   
            return {"error": f"Ticket '{ticket_id}' not found"}
        response.raise_for_status()     
        return response.json()
                                                                    
                                            
async def list_tickets(query: str) -> list[dict]:                    
    """                                                   
    CRUD tool — lists all support tickets for a customer from BU4.   
    """
    customer_id = await _extract_customer_id(query)                  
    if not customer_id:                                   
        return [{"error": "Could not extract customer ID from query"}]                                    
                                        
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


    async with httpx.AsyncClient as client:
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
    
async def search_resolved_tickets(query: str) -> list[str]:


    async with httpx.AsyncClient as client:
        response = await client.post(
            f"{_BASE_URL}/rag.search",
            json={
                "query": query,
                "top_k": settings.rag_top_k,
                "filter": {"type": "resolved_ticket"}
            },
            timeout=15.0
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [chunk["text"] for chunk in data.get("results", [])]
                                                

import httpx                                                         
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI                              
                                                        
from shared.config import settings                                   

_llm = ChatOpenAI(                                                   
    model=settings.openai_chat_model,                     
    temperature=0,                             
    api_key=settings.openai_api_key,        
)                                       

_BASE_URL = settings.bu3_base_url                                    
   
                                                                       
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
                                                            
                                                 
async def _extract_invoice_id(query: str) -> str | None:
    response = await _llm.ainvoke([                                  
        SystemMessage(content=(
            "Extract the invoice ID from the user query. "           
            "Invoice IDs are alphanumeric strings like 'INV-001', 'INVOICE-123', or a MongoDB ObjectId. "        
            "Reply with ONLY the invoice ID and nothing else. "
            "If no invoice ID is present, reply with: NONE"
        )),                                                          
        HumanMessage(content=query),
    ])                                                               
    result = response.content.strip()                     
    return None if result == "NONE" else result
                                                                       
   
async def get_subscription(query: str) -> dict:                      
    """                                                   
    CRUD tool — fetches the subscription plan for a customer from 
BU3.                                        
    """                                 
    customer_id = await _extract_customer_id(query)
    if not customer_id:                                              
        return {"error": "Could not extract customer ID from query"}
                                                                    
    async with httpx.AsyncClient() as client:             
        response = await client.get(           
            f"{_BASE_URL}/subscriptions/{customer_id}",              
            timeout=10.0,
        )                                                            
        if response.status_code == 404:                   
            return {"error": f"Subscription for customer '{customer_id}' not found"}             
        response.raise_for_status()
        return response.json()                                       
   
                                                                       
async def list_invoices(query: str) -> list[dict]:        
    """                                        
    CRUD tool — lists all invoices for a customer from BU3.          
    """
    customer_id = await _extract_customer_id(query)                  
    if not customer_id:                                   
        return [{"error": "Could not extract customer ID from query"}]                                    
                                        
    async with httpx.AsyncClient() as client:
        response = await client.get(                                 
            f"{_BASE_URL}/invoices/{customer_id}",
            timeout=10.0,                                            
        )                                                 
        if response.status_code == 404:        
            return []                       
        response.raise_for_status()     
        return response.json()
                                                                       
                                              
async def search_billing_statements(query: str) -> list[str]:        
    """                                                   
    RAG tool — semantic search over BU3 billing statements and plan  
documents.
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
import httpx                                                                                    
                                                        
from shared.config import settings                                                                         

_BASE_URL = settings.bu3_base_url
                                                                       
   
async def get_subscription(customer_id: str) -> dict:                      
    """                                                   
    CRUD tool — fetches the subscription plan for a customer from 
BU3.                                        
    """
                                                                    
    async with httpx.AsyncClient() as client:             
        response = await client.get(           
            f"{_BASE_URL}/subscriptions/{customer_id}",              
            timeout=10.0,
        )                                                            
        if response.status_code == 404:                   
            return {"error": f"Subscription for customer '{customer_id}' not found"}             
        response.raise_for_status()
        return response.json()                                       
   
                                                                       
async def list_invoices(customer_id: str) -> list[dict]:        
    """                                        
    CRUD tool — lists all invoices for a customer from BU3.          
    """                                  
                                        
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
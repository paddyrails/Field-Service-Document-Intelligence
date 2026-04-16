import re                                                                       
import json                                                                     
                                                                            
from langchain_core.messages import HumanMessage, SystemMessage                 
from langchain_openai import ChatOpenAI                                       

from shared.config import settings                                              
                                        
PII_PATTERNS = [                                                                
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),                               
    (r'\b\d{16}\b', '[CARD_REDACTED]'),     
    (r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b', '[EMAIL_REDACTED]'),                      
    (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]'),               
]                                                                               
                                                                                
BLOCKED_PHRASES = [                                                             
    "ignore previous",                                                          
    "ignore above",                                                             
    "disregard previous",                                                       
    "system prompt",                                                          
    "jailbreak",                                                                
    "bypass",
]                                                                               
                                                                            
DOMAIN_KEYWORDS = [
    "patient", "visit", "care", "nursing", "therapy", "billing",                
    "invoice", "ticket", "support", "contract", "customer",
    "onboarding", "kyc", "subscription", "appointment", "insurance",            
    "schedule", "service", "maintenance", "claim", "status",                  
]                                                                               
                                                                                
# Lazy singleton so importing guardrails doesn't force an OpenAI connection     
_grounding_llm: ChatOpenAI | None = None                                        
                                                                                
def _get_grounding_llm() -> ChatOpenAI:                                         
    global _grounding_llm               
    if _grounding_llm is None:                                                  
        _grounding_llm = ChatOpenAI(                                            
            model=settings.openai_chat_model,
            temperature=0,                                                      
            api_key=settings.openai_api_key,                                  
        )
    return _grounding_llm                                                       

                                                                                
def detect_prompt_injection(text: str) -> str | None:                         
    """Return error message if suspicious phrase detected, else None."""
    lower = text.lower()                                                        
    for phrase in BLOCKED_PHRASES:      
        if phrase in lower:                                                     
            return f"BLOCKED: prompt injection pattern detected ('{phrase}')"   
    return None                             
                                                                                
                                                                            
def check_topic_relevance(text: str) -> str | None:                             
    """Reject queries unrelated to RiteCare domain."""
    lower = text.lower()                                                        
    if not any(k in lower for k in DOMAIN_KEYWORDS):                          
        return "BLOCKED: query is not related to RiteCare services"
    return None                                                                 
                                                                                
                                                                                
def redact_pii(text: str) -> str:                                               
    """Redact PII from text."""                                               
    for pattern, replacement in PII_PATTERNS:                                   
        text = re.sub(pattern, replacement, text)                             
    return text
                                                                                
                                            
async def check_grounding(response: str, retrieved_docs: list[str]) -> dict:    
    """Check if response is grounded in retrieved context."""                 
    context = "\n".join(retrieved_docs) if retrieved_docs else "(no context)"   
    prompt = f"""Evaluate if the response is grounded in the provided context.
Context:                                                                        
{context}                                                                       
                                                                                
Response:                                                                       
{response}                                                                      
                                                                                
Respond with EXACTLY this JSON format:                                        
{{"grounded": true or false, "reason": "one sentence explanation"}}
"""                                         
                                        
    result = await _get_grounding_llm().ainvoke([
        SystemMessage(content="You are a strict grounding evaluator."),         
        HumanMessage(content=prompt),
    ])                                                                          
                                                                            
    try:                                                                        
        text = (result.content or "").strip()                                 
        if text.startswith("```"):                                              
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)                                                 
    except (json.JSONDecodeError, IndexError):                                
        return {"grounded": True, "reason": "Could not parse grounding check"}
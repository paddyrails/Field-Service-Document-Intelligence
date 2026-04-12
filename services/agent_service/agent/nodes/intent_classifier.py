from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.state import AgentState
from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0,
    api_key=settings.openai_api_key
)

CLASSIFIER_PROMPT = """
You are a query router for RiteCare, a field service company.        
                                                        
Given a user query, identify:                  
1. Which business unit(s) are relevant: BU1 (onboarding), BU2 
(sales/maintenance), BU3 (billing), BU4 (support)                    
2. What type of tools are needed: CRUD (live data lookup), RAG 
(document search), or BOTH                                           
                                                                    
Respond in this exact format and nothing else: 
INTENT: <BU1|BU2|BU3|BU4|BU1+BU2|...>, TOOLS: <CRUD|RAG|BOTH>        
                                                        
Examples:                                                            
- "What is the KYC status of customer C123?" → INTENT: BU1, TOOLS: 
CRUD                                                                 
- "How do I service the X200 pump?" → INTENT: BU2, TOOLS: RAG
- "Has this pressure fault been seen before and is ticket T99 still  
open?" → INTENT: BU2+BU4, TOOLS: BOTH  
"""

async def intent_classifier(state: AgentState) -> dict:
    user_message = state["messages"][-1]

    response = await _llm.ainvoke([
        SystemMessage(content=CLASSIFIER_PROMPT),
        HumanMessage(content=user_message.content)
    ])

    return {"intent": response.content.strip()}
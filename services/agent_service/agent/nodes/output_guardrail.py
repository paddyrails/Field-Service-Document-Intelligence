import json 

from agent.state import AgentState
from shared.guardrails import check_grounding, redact_pii

#Tool-result "type values from tool_executor that represent retrived docs"
RAG_RESULT_TYPES = {"RAG", "rag", "search"}

MAX_GROUNDING_RERIES = 1

SAFE_RESPONSE = (
    "I'm sorry, I couldn't find enough information in our document "
    "to answer that reliably. Please contact support for further assistance"
)

def _extract_retrieved_docs(tool_results: list[dict]) -> list[str]:
    """
    Pull text chunks out of RAG tool results for grounding checks
    """
    docs: list[str] = []
    for item in tool_results or []:
        if item.get("type", "").upper() not in {t.upper() for t in RAG_RESULT_TYPES}:
            continue
        result = item.get("result")
        if isinstance(result, list):                                            
            docs.extend(str(d.get("text", d)) if isinstance(d, dict) else str(d) for d in result)                                                               
        elif isinstance(result, dict) and "results" in result:                
            docs.extend(
                str(d.get("text", d)) if isinstance(d, dict) else str(d)
                for d in result["results"]
            )                                                    
        elif result is not None:
            docs.append(str(result))                                            
    return docs 

async def output_guardrail(state: AgentState) -> dict:
    """Redact PII and ground-check the response against retrieved context"""
    final = state.get("final_response", "") or ""
    if not final:
        return {}
    
    #PII redaction
    final = redact_pii(final)

    #Grounding check only if RAG docs were retrived this turn
    docs = _extract_retrieved_docs(state.get("tool_results", []))
    if docs and final.strip():
        verdict = await check_grounding(final, docs)
        if not verdict.get("grounded", True):
            retries = state.get("grounding_retries", 0)

            if retries < MAX_GROUNDING_RERIES:
                #send back to responder with feedback
                return {
                    "final_response": "",
                    "grounding_retries": retries + 1,
                    "grounding_feedback": verdict.get("reason", "Response not grounded in retrived documents")                    
                }
            #Max retries exhausted - return safe fallback
            return {"final_response": SAFE_RESPONSE}            

    return {"final_response": final}